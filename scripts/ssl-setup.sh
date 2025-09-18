#!/bin/bash

# SSL Setup Script for Neuro Maze Bot
# Usage: ./ssl-setup.sh your-domain.com

set -e

DOMAIN=$1
EMAIL="markberezhnoy27@gmail.com"  # Замените на ваш email

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 bot.yourdomain.com"
    exit 1
fi

echo "🔐 Setting up SSL for domain: $DOMAIN"

# Создаем временную конфигурацию Nginx для получения сертификата
cat > /tmp/nginx-temp.conf << EOF
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://\$host\$request_uri;
        }
    }
}
EOF

# Останавливаем основной Nginx если запущен
docker-compose stop nginx || true

# Запускаем временный Nginx для получения сертификата
docker run --rm -d \
    --name nginx-temp \
    -p 80:80 \
    -v /tmp/nginx-temp.conf:/etc/nginx/nginx.conf \
    -v /var/www/certbot:/var/www/certbot \
    nginx:alpine

# Создаем директорию для certbot
mkdir -p /var/www/certbot

# Получаем сертификат
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN

# Останавливаем временный Nginx
docker stop nginx-temp

# Обновляем конфигурацию Nginx с правильным доменом
sed -i "s/your-domain.com/$DOMAIN/g" nginx/nginx.conf

echo "✅ SSL certificate obtained successfully!"
echo "🔧 Don't forget to:"
echo "   1. Update nginx/nginx.conf with your domain: $DOMAIN"
echo "   2. Set up automatic renewal with:"
echo "      docker run --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew"
echo "   3. Add to crontab for auto-renewal:"
echo "      0 12 * * * docker run --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew --quiet" 
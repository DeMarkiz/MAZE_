#!/bin/bash

# SSL Renewal Script for Neuro Maze Bot
# Add to crontab: 0 12 * * * /path/to/scripts/renew-ssl.sh

set -e

echo "🔄 Starting SSL certificate renewal..."

# Проверяем, нужно ли обновление
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    certbot/certbot renew --dry-run

if [ $? -eq 0 ]; then
    echo "✅ Certificates are up to date"
    exit 0
fi

echo "📝 Renewing certificates..."

# Обновляем сертификаты
docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    certbot/certbot renew --quiet

# Перезапускаем Nginx для применения новых сертификатов
docker-compose restart nginx

echo "✅ SSL certificates renewed successfully!"
echo "🔄 Nginx restarted with new certificates" 
# 🚀 Развертывание Neuro Maze Bot

## 📋 Требования

- Docker и Docker Compose
- Домен (например, `bot.yourdomain.com`)
- Сервер с публичным IP
- YouMoney аккаунт и API ключи

## 🔧 Настройка

### 1. Подготовка сервера

```bash
# Клонируем репозиторий
git clone <your-repo>
cd neuro_mazу_0

# Делаем скрипты исполняемыми
chmod +x scripts/ssl-setup.sh
chmod +x scripts/renew-ssl.sh
```

### 2. Настройка переменных окружения

Создайте файл `.env`:

```env
# База данных
DB_USER=postgres
DB_PASS=your_secure_password
DB_NAME=neuro_maze

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://your-domain.com

# YouMoney
YOOMONEY_SHOP_ID=your_shop_id
YOOMONEY_SECRET_KEY=your_secret_key
YOOMONEY_TOKEN=your_token

# OpenAI
OPENAI_API_KEY=your_openai_key

# Redis
REDIS_URL=redis://redis:6379
```

### 3. Настройка домена

1. **Настройте DNS** - добавьте A-запись для вашего домена, указывающую на IP сервера
2. **Получите SSL сертификат**:

```bash
# Замените your-domain.com на ваш домен
./scripts/ssl-setup.sh your-domain.com
```

3. **Обновите конфигурацию Nginx** - замените `your-domain.com` на ваш домен в `nginx/nginx.conf`

### 4. Настройка YouMoney

1. **В YouMoney кабинете**:
   - Добавьте webhook URL: `https://your-domain.com/webhook/yoomoney`
   - Настройте уведомления о платежах

2. **Проверьте API ключи** в `.env` файле

### 5. Запуск приложения

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f app
```

### 6. Настройка Telegram Webhook

После запуска приложения, webhook будет автоматически настроен в `main.py`.

## 🔄 Автоматическое обновление SSL

Добавьте в crontab для автоматического обновления сертификатов:

```bash
# Открыть crontab
crontab -e

# Добавить строку (замените путь на ваш)
0 12 * * * /path/to/neuro_mazу_0/scripts/renew-ssl.sh
```

## 📊 Мониторинг

### Проверка здоровья приложения

```bash
# Проверка health endpoint
curl https://your-domain.com/health

# Проверка логов
docker-compose logs app
docker-compose logs nginx
```

### Проверка платежей

```bash
# Подключение к БД
docker-compose exec db psql -U postgres -d neuro_maze

# Проверка платежей
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;
```

## 🔒 Безопасность

### Рекомендации:

1. **Измените пароли** по умолчанию
2. **Настройте firewall** - откройте только порты 80, 443
3. **Регулярно обновляйте** зависимости
4. **Мониторьте логи** на подозрительную активность
5. **Настройте backup** базы данных

### Firewall (UFW):

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## 🐛 Устранение неполадок

### Проблемы с SSL:

```bash
# Проверка сертификатов
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot certificates

# Принудительное обновление
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew --force-renewal
```

### Проблемы с YouMoney:

```bash
# Проверка логов webhook
docker-compose logs app | grep -i webhook

# Тестирование API
curl -X POST https://your-domain.com/webhook/yoomoney \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test=1"
```

### Проблемы с базой данных:

```bash
# Проверка подключения
docker-compose exec db pg_isready -U postgres

# Восстановление из backup
docker-compose exec db psql -U postgres -d neuro_maze < backup.sql
```

## 📈 Масштабирование

### Для высоких нагрузок:

1. **Добавьте Redis Cluster**
2. **Настройте балансировщик нагрузки**
3. **Используйте CDN** для статических файлов
4. **Настройте мониторинг** (Prometheus + Grafana)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Проверьте статус сервисов: `docker-compose ps`
3. Проверьте health endpoint: `curl https://your-domain.com/health`
4. Создайте issue в репозитории с логами 
# Django Docker Production Neuro Maze

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

Производственный шаблон для Django-приложений с Docker, Nginx, Gunicorn и PostgreSQL. Включает готовую конфигурацию для быстрого развертывания продакшен-окружения.

## Особенности проекта

- 🐳 Полностью Docker-изированное окружение
- 🔒 Готовые настройки для продакшена
- 🌐 Настроенный Nginx
- 🔄 CORS headers для API
- 📦 Переменные окружения через .env файл
- ⚡ Gunicorn с оптимизированными параметрами
- 🐘 PostgreSQL для производственного использования
- 🔧 Миграции и сборка статики при запуске

## Технологический стек

- **Backend**: Django 5.x
- **Web Server**: Nginx
- **WSGI Server**: Gunicorn
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker + Docker Compose
- **Environment Management**: python-dotenv
- **Security**: CORS headers

## Быстрый старт

### Настройка окружения

1. Создайте файл окружения на основе примера:
   ```bash
   cp .env.example .env
   ```
2. Отредактируйте файл `.env` по примеру

### Запуск проекта

```bash
docker-compose up --build -d
```

После запуска приложение будет доступно по адресу: [http://localhost:8000](http://localhost:8000)


## Команды управления

| Команда | Описание |
|---------|----------|
| `docker-compose up --build -d` | Собрать и запустить контейнеры |
| `docker-compose down` | Остановить и удалить контейнеры |
| `docker-compose logs -f app` | Просмотр логов приложения |
| `docker-compose exec app python manage.py migrate` | Применить миграции БД |
| `docker-compose exec app python manage.py createsuperuser` | Создать суперпользователя |
| `docker-compose restart nginx` | Перезапустить Nginx |

## Настройка CORS

CORS уже настроен через `django-cors-headers`. Для изменения настроек отредактируйте:

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "http://localhost:3000",
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
```

## Оптимизация

Проект включает готовые оптимизации для продакшена:

- Gunicorn с 4 воркерами и 2 потоками
- Nginx с кешированием статики
- Сжатие статических файлов
- HTTPS редирект
- Заголовки безопасности
- Оптимизированные настройки Django для продакшена

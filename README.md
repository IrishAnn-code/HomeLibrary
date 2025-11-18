cat > README.md << 'EOF'
# 📚 HomeLibrary - Система управления домашней библиотекой

Веб-приложение для учета домашних книг с поддержкой:
- 🔐 Авторизация и регистрация пользователей
- 📖 Управление книгами и библиотеками
- 🔍 Поиск по автору, названию, жанру
- 🤖 Telegram бот (в разработке)

## 🚀 Технологии

- **Backend**: FastAPI, SQLAlchemy (async), Pydantic
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Auth**: JWT tokens, bcrypt
- **Frontend**: Jinja2 templates
- **Bot**: aiogram (планируется)

## 📦 Установка
```bash
# Клонируйте репозиторий
git clone https://github.com/YOUR_USERNAME/HomeLibrary.git
cd HomeLibrary

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Создайте .env файл
cp .env.example .env
# Отредактируйте .env и добавьте свой SECRET_KEY

# Примените миграции
alembic upgrade head

# Запустите сервер
uvicorn app.main:app --reload
```

## 🔧 Конфигурация

Создайте файл `.env` на основе `.env.example`:
```env
SECRET_KEY=your-secret-key-here-min-32-chars
DATABASE_URL=sqlite+aiosqlite:///./homelibrary.db
DEBUG=True
```

## 📖 API Документация

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗂 Структура проекта
```
app/
├── core/          # Конфигурация, исключения
├── database/      # Подключение к БД, auth
├── models/        # SQLAlchemy модели
├── routers/       # FastAPI роутеры (API + HTML)
├── schemas/       # Pydantic схемы
├── services/      # Бизнес-логика
├── templates/     # Jinja2 шаблоны
└── utils/         # Вспомогательные функции
```

## 🎯 TODO

- [ ] Добавить тесты (pytest)
- [ ] Telegram бот integration
- [ ] OCR для распознавания книг
- [ ] Экспорт в Excel/PDF
- [ ] Docker контейнеризация
- [ ] Деплой на VPS

## 📝 Лицензия

MIT
EOF



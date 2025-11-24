from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from typing import Annotated
import logging

from app.database.auth import get_current_user_optional
from app.models import User
from app.routers.api import api_books, api_users, api_libraries
from app.routers.html import html_book, html_user, html_library
from app.core.config import settings
from app.utils.flash import get_flashed_messages

# ✅ Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ✅ Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])

tags_metadata = [
    {"name": "default", "description": "Приветствие на главной странице"},
    {"name": "Users (API)"},
    {"name": "Users (HTML)"},
    {"name": "Books (API)"},
    {"name": "Books (HTML)"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    logger.info(f"📊 Debug mode: {settings.DEBUG}")
    logger.info(f"🔐 CORS origins: {settings.ALLOWED_ORIGINS}")

    yield  # Приложение работает

    # Shutdown
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Проект на FastAPI: Домашняя библиотека",
    version="7.10",
    openapi_tags=tags_metadata,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


# ✅ Привязываем limiter к app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Flash messages
app.add_middleware(
    SessionMiddleware, secret_key=settings.SECRET_KEY, max_age=7 * 24 * 3600  # 7 дней
)

# ✅ Добавляем SlowAPI middleware
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Из .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Шаблоны
templates = Jinja2Templates(directory="app/templates")
CurrentUser = Annotated[User, Depends(get_current_user_optional)]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: CurrentUser):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Главная страница",
            "user": current_user,
            "messages": get_flashed_messages(request),
        },
    )


# ✅ Health check endpoint
@app.get("/health", tags=["default"])
async def health_check():
    """Проверка состояния API"""
    return {"status": "healthy", "app": settings.APP_NAME, "version": "8.0.0"}


app.include_router(api_users.router)
app.include_router(api_books.router)  # Позволит подключать другие роутеры
app.include_router(api_libraries.router)
app.include_router(html_user.router)
app.include_router(html_book.router)
app.include_router(html_library.router)


# запуск python3 -m uvicorn app.main:app
# uvicorn app.main:app --reload

# alembic revision --autogenerate -m 'Initial migration'
# alembic -c alembic.ini upgrade head
# pip install -r requirements.txt


#

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


from app.routers.api import api_books, api_users, api_libraries
from app.routers.html import hlml_books, html_users, html_libraries
from app.core.config import settings

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# ✅ Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Rate limiter
limiter = Limiter(key_func=get_remote_address)

tags_metadata = [
    {"name": "default", "description": "Приветствие на главной странице"},
    {"name": "Users (API)"},
    {"name": "Users (HTML)"},
    {"name": "Books (API)"},
    {"name": "Books (HTML)"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description="Проект на FastAPI: Домашняя библиотека",
    version="7.10",
    openapi_tags=tags_metadata,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Из .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Шаблоны
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Главная страница"}
    )

# ✅ Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    logger.info(f"📊 Debug mode: {settings.DEBUG}")
    logger.info(f"🔐 CORS origins: {settings.ALLOWED_ORIGINS}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")

app.include_router(api_users.router)
app.include_router(api_books.router)  # Позволит подключать другие роутеры
app.include_router(api_libraries.router)
app.include_router(html_users.router)
app.include_router(hlml_books.router)
app.include_router(html_libraries.router)


# ✅ Health check endpoint
@app.get("/health", tags=['default'])
async def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "8.0.0"
    }

# запуск python3 -m uvicorn app.main:app
# uvicorn app.main:app --reload

# alembic revision --autogenerate -m 'Initial migration'
# alembic -c alembic.ini upgrade head
# pip install -r requirements.txt

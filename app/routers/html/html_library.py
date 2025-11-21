from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.services import library_service
from app.utils.flash import get_flashed_messages, flash

router = APIRouter(prefix="/library", tags=["Libraries (HTML)"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_class=HTMLResponse)
async def libraries_list(request: Request, db: DBType, current_user: CurrentUser):
    """Список всех библиотек пользователя"""

    libraries = await library_service.list_user_libraries(db, current_user.id)
    return templates.TemplateResponse(
        "libraries/list.html",
        {
            "request": request,
            "libraries": libraries,
            "user": current_user,
            "title": "Мои библиотеки",
            "messages": get_flashed_messages(request)
        }
    )


@router.get("/create", response_class=HTMLResponse)
async def create_library_page(request: Request, current_user: CurrentUser):
    """Страница создания библиотеки"""
    return templates.TemplateResponse(
        "libraries/create.html",
        {"request": request, "user": current_user}
    )


@router.post("/create")
async def create_library_submit(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    name: str = Form(...),
    password: str | None = Form(None)
):
    """Обработка создания библиотеки"""
    try:
        await library_service.create_library(db, name, password, current_user.id)
        flash(request, f"Библиотека для {current_user.username} успешно создана!", "success")
        return RedirectResponse(url="/library/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "libraries/create.html",
            {"request": request, "error": str(e), "user": current_user}
        )


@router.get("/{library_id}", response_class=HTMLResponse)
async def library_detail(
        request: Request,
        db: DBType,
        library_id: int,
        current_user: CurrentUser
):
    """Страница библиотеки с книгами"""
    library = await library_service.get_library(db, library_id)
    books = await library_service.all_books_in_lib(db, library_id)

    return templates.TemplateResponse(
        "libraries/detail.html",
        {
            "request": request,
            "library": library,
            "books": books,
            "user": current_user
        }
    )

@router.get("/{library_id}/join", response_class=HTMLResponse)
async def join_library_page(request: Request, library_id: int, current_user: CurrentUser):
    """Страница присоединения к библиотеке"""
    return templates.TemplateResponse(
        "libraries/join.html",
        {"request": request, "library_id": library_id, "user": current_user}
    )

@router.post("/{library_id}/join")
async def join_library_submit(
    request: Request,
    db: DBType,
    library_id: int,
    current_user: CurrentUser,
    password: str | None = Form(None)
):
    """Присоединиться к библиотеке"""
    try:
        await library_service.join_library(db, library_id, password, current_user.id)
        return RedirectResponse(url=f"/library/{library_id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "libraries/join.html",
            {"request": request, "error": str(e), "user": current_user}
        )
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
from typing import Annotated

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
            "messages": get_flashed_messages(request),
            "libraries": libraries,
            "user": current_user,
            "title": "Мои библиотеки",
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_library_page(request: Request, current_user: CurrentUser):
    """Страница создания библиотеки"""
    return templates.TemplateResponse(
        "libraries/create.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "user": current_user,
        },
    )


@router.post("/create")
async def create_library_submit(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    name: str = Form(...),
    password: str | None = Form(None),
):
    """Обработка создания библиотеки"""
    try:
        await library_service.create_library(db, name, password, current_user.id)
        flash(
            request,
            f"Библиотека для {current_user.username} успешно создана!",
            "success",
        )
        return RedirectResponse(url="/library/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "libraries/create.html",
            {
                "request": request,
                "messages": get_flashed_messages(request),
                "error": str(e),
                "user": current_user,
            },
        )


@router.get("/search", response_class=HTMLResponse)
async def search_libraries(
    request: Request, db: DBType, current_user: CurrentUser, q: str = ""
):
    """Поиск библиотек для присоединения"""
    logger.info(f"🎯 START SEARCH: query='{q}'")
    libraries = await library_service.search_libraries_to_join(db, current_user.id, q)
    return templates.TemplateResponse(
        "libraries/search.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "libraries": libraries,
            "query": q,
            "user": current_user,
        },
    )


@router.get("/{library_id}/join", response_class=HTMLResponse)
async def join_library_page(
    request: Request, db: DBType, library_id: int, current_user: CurrentUser
):
    """Страница присоединения к библиотеке"""
    library = await library_service.get_library(db, library_id)
    logger.info(
        f"🔍22222 Checking membership: user_id={current_user.id}, library_id={library_id}"
    )

    if not library:
        flash(request, "Библиотека не найдена", "error")
        return RedirectResponse(url="/library/search", status_code=303)

    is_member = await library_service.is_library_member(db, current_user.id, library_id)

    if is_member:
        flash(request, "Вы уже состоите в этой библиотеке", "info")
        return RedirectResponse(url=f"/library/", status_code=303)

    return templates.TemplateResponse(
        "libraries/join.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "library": library,
            "user": current_user,
        },
    )


@router.post("/{library_id}/join")
async def join_library_submit(
    request: Request,
    db: DBType,
    library_id: int,
    current_user: CurrentUser,
    password: str | None = Form(None),
):
    """Присоединиться к библиотеке"""
    try:
        library = await library_service.join_library(
            db, library_id, password, current_user.id
        )
        flash(request, f"Вы присоединились к библиотеке '{library.name}'", "success")
        return RedirectResponse(url=f"/library/", status_code=303)
    except HTTPException as e:
        flash(request, f"{e}", "error")
        return RedirectResponse(url=f"/library/{library_id}/join", status_code=303)


@router.get("/{library_id}/edit", response_class=HTMLResponse)
async def edit_library_page(
    request: Request, db: DBType, library_id: int, current_user: CurrentUser
):
    """Страница редактирования библиотеки"""
    library = await library_service.get_library(db, library_id)
    if not library:
        flash(request, "Библиотека не найдена", "error")
        return RedirectResponse(url="/library/", status_code=303)

    owner_username = await library_service.get_username_by_lib_id(db, library_id)
    if not owner_username:
        flash(request, "Владелец библиотеки не найден", "error")

    return templates.TemplateResponse(
        "libraries/edit.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "library": library,
            "user": current_user,
            "owner_username": owner_username,
        },
    )


@router.post("/{library_id}/edit")
async def edit_library_submit(
    request: Request,
    db: DBType,
    library_id: int,
    current_user: CurrentUser,
    new_name: str = Form(),
):
    """Обработка редактирования библиотеки"""
    try:
        edit_library_name = await library_service.update_name(
            db, new_name, library_id, current_user.id
        )
        logger.info(f"ℹ️ Успешно: {edit_library_name}")
        flash(request, "Название библиотеки обновлено", "success")
        return RedirectResponse(url=f"/library/{library_id}", status_code=303)
    except Exception as e:
        flash(request, f"Ошибка: {str(e)}", "error")
        return RedirectResponse(url=f"/library/{library_id}/edit", status_code=303)


@router.post("/{library_id}/leave")
async def library_leave_submit(
    request: Request, db: DBType, library_id: int, current_user: CurrentUser
):
    """Выйти из библиотеки"""
    success, message = await library_service.leave_library(
        db, library_id, current_user.id
    )

    if success:
        flash(request, message, "success")
        return RedirectResponse(url="/library/", status_code=303)
    else:
        flash(request, message, "error")
        return RedirectResponse(url="/library/{library_id}", status_code=303)


@router.post("/{library_id}/delete")
async def delete_library_submit(
    request: Request, db: DBType, library_id, current_user: CurrentUser
):
    """Удалить библиотеку"""
    ## когда появится админ-панель, добавить в список current_user.is_admin
    success, message = await library_service.delete_library(
        db, library_id, current_user.id
    )

    if success:
        flash(request, message, "success")
        return RedirectResponse(url="/library/", status_code=303)
    else:
        flash(request, message, "error")
        return RedirectResponse(url="/library/{library_id}", status_code=303)


@router.get("/{library_id}", response_class=HTMLResponse)
async def library_detail(
    request: Request, db: DBType, library_id: int, current_user: CurrentUser
):
    """Страница библиотеки с книгами"""
    is_member = await library_service.is_library_member(db, current_user.id, library_id)
    if is_member:
        library = await library_service.get_library(db, library_id)
        books_with_status = await library_service.get_library_books_with_status(
            db, library_id, current_user.id
        )

        logger.info(f"!!!!!🔍 {books_with_status}")
        return templates.TemplateResponse(
            "libraries/detail.html",
            {
                "request": request,
                "messages": get_flashed_messages(request),
                "library": library,
                "books_with_status": books_with_status,
                "user": current_user,
            },
        )
    else:
        flash(request, "Вы не участник этой библиотеки", "error")
        return RedirectResponse(url="/library", status_code=303)

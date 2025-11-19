from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.services import library_service


router = APIRouter(prefix="/library", tags=["Libraries (HTML)"])
templates = Jinja2Templates(directory="app/templates")

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_class=HTMLResponse)
async def libraries_page(
    request: Request,
    db: DBType,
    current_user: CurrentUser
):
    """Страница со списком библиотек"""
    libraries = await library_service.list_user_libraries(db, current_user.id)
    return templates.TemplateResponse(
        "libraries/list.html",
        {
            "request": request,
            "libraries": libraries,
            "user": current_user
        }
    )
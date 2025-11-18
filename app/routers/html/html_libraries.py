from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.services.library_service import list_user_libraries

router = APIRouter(prefix="/library", tags=["Libraries (HTML)"])
templates = Jinja2Templates(directory="app/templates")

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AsyncSession, Depends(get_current_user)]


@router.get("/")
async def all_libraries(request: Request, db: DBType, current_user: CurrentUser):
    libs = list_user_libraries(db, current_user.id)
    return templates.TemplateResponse(
        "libraries/list.html", {"request": request, "libs": libs}
    )

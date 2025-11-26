from app.models.user import User
from app.models.book import Book
from app.models.user_library import UserLibrary
from app.models.library import Library
from app.models.user_book_status import UserBookStatus
from app.models.comments import Comments
from app.database.db import Base

from sqlalchemy.schema import CreateTable


if __name__ == "__main__":
    for table in Base.metadata.sorted_tables:
        print(CreateTable(table))

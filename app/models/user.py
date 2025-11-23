from app.database.db import Base
from sqlalchemy import Column, String, Integer, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


# ---------- User ---------- #
class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("username", name="uq_username"),
        {"extend_existing": True, "sqlite_autoincrement": True},
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    tg_id = Column(Integer, nullable=True)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Связи:
    # 1. Пользователь может быть участником нескольких библиотек
    libraries_assoc = relationship(
        "UserLibrary", back_populates="user", cascade="all, delete-orphan"
    )

    # 2. Через таблицу user_library получаем все библиотеки, где участвует
    libraries = relationship(
        "Library", secondary="user_library", back_populates="users", viewonly=True
    )

    # 3. Пользователь может быть владельцем библиотек
    owned_libraries = relationship(
        "Library", back_populates="owner", foreign_keys="Library.owner_id"
    )

    # 4. Получаем все книги, которые добавил пользователь
    books = relationship("Book", back_populates="user")  # , cascade="all, delete"

    # 5. Даем доступ для статусов чтения
    book_read_statuses = relationship("UserBookStatus", back_populates="user")

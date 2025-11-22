from app.database.db import Base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import timezone, datetime


# ---------- Library ---------- #
class Library(Base):
    __tablename__ = "library"
    __table_args__ = {"extend_existing": True, "sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=True, index=True)
    password_hash = Column(String, nullable=True)  # None для открытых библиотек
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Связи:
    # 1. Владелец библиотеки (1 владелец)
    owner = relationship("User", back_populates="owned_libraries", overlaps="libraries")
    # 2. Книги, которые принадлежат библиотеке (Много книг)
    books = relationship(
        "Book", back_populates="library", cascade="all, delete-orphan", overlaps="users"
    )
    # 3. (промежуточная таблица)
    users_assoc = relationship(
        "UserLibrary",
        back_populates="library",
        cascade="all, delete-orphan",
        overlaps="users",
    )
    # 4.
    users = relationship(
        "User",
        secondary="user_library",
        back_populates="libraries",
        overlaps="users_assoc,libraries_assoc",
    )

    @property
    def is_private(self) -> bool:
        """Проверка, является ли библиотека приватной"""
        return self.password_hash is not None

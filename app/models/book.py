from datetime import datetime, timezone

from app.database.db import Base
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.enum import ReadStatus


# ---------- Book ---------- #
class Book(Base):
    __tablename__ = "book"
    __table_args__ = {"extend_existing": True, "sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String)
    title = Column(String)
    description = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    color = Column(String, nullable=True)

    lib_address = Column(String)  # institut.13
    room = Column(String, nullable=True)  #  saloon
    shelf = Column(String, nullable=True)  # 3rd shelf

    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    library_id = Column(Integer, ForeignKey("library.id"), index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)

    # 🔗 связи
    library = relationship("Library", back_populates="books")
    user = relationship("User", back_populates="books")
    user_statuses = relationship(
        "UserBookStatus", back_populates="book", cascade="all, delete-orphan"
    )

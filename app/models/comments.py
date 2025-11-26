from app.database.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone



# ---------- Comments ---------- #
class Comments(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index('ix_comments_book_id', 'book_id'),
        Index('ix_comments_user_id', 'user_id'),
        Index('ix_comments_created_at', 'created_at'),
        {"extend_existing": True, "sqlite_autoincrement": True})

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    user_id = Column(Integer, ForeignKey("user.id"))
    book_id = Column(Integer, ForeignKey("book.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Связи:
    user = relationship("User", back_populates="comments_assoc")
    book = relationship("Book", back_populates="comments_assoc")
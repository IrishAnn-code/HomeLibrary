from app.database.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


class UserBookStatus(Base):
    """Статус чтения книги для конкретного пользователя"""

    __tablename__ = "user_book_status"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book"),
        {"extend_existing": True},
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)
    read_status = Column(String, default="not_read")

    # 🔗 связи
    user = relationship("User", back_populates="book_read_statuses")
    book = relationship("Book", back_populates="user_statuses")

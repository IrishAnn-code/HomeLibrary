from app.database.db import Base
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.enum import LibraryRole


# ---------- Connection User ↔ Library  ---------- #


class UserLibrary(Base):
    __tablename__ = "user_library"
    __table_args__ = {"extend_existing": True, "sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    library_id = Column(Integer, ForeignKey("library.id"), nullable=False)
    role = Column(SQLEnum(LibraryRole), default=LibraryRole.MEMBER)

    # 🔗 двусторонние связи
    user = relationship("User", back_populates="libraries_assoc", overlaps="libraries")
    library = relationship("Library", back_populates="users_assoc", overlaps="users")

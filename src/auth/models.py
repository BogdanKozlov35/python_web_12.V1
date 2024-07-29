from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
# from src.contacts.models import Base

from src.conf.config import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, index=True, unique=True)
    email: Mapped[str] = mapped_column(String, index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="owner")
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=True)
    role: Mapped["Role"] = relationship("Role", lazy="selectin")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)


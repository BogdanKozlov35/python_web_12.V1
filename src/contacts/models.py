from sqlalchemy import String, Integer, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column


from src.auth.models import User, Role

from src.conf.config import Base


class Contact(Base):
    __tablename__ = 'contacts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firstname: Mapped[str] = mapped_column(String, index=True)
    lastname: Mapped[str] = mapped_column(String, index=True)
    birthday: Mapped[Date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    emails: Mapped[list["Email"]] = relationship("Email", back_populates="contact")
    phones: Mapped[list["Phone"]] = relationship("Phone", back_populates="contact")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="contacts")


class Email(Base):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey('contacts.id'))

    contact: Mapped["Contact"] = relationship("Contact", back_populates="emails")


class Phone(Base):
    __tablename__ = 'phones'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String, index=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey('contacts.id'))

    contact: Mapped["Contact"] = relationship("Contact", back_populates="phones")



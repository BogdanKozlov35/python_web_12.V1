from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime

from pydantic.v1 import validator


class EmailSchema(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class PhoneSchema(BaseModel):
    phone: str

    class Config:
        from_attributes = True


class ContactSchema(BaseModel):
    firstname: str = Field(..., min_length=3, max_length=50)
    lastname: str = Field(..., min_length=3, max_length=50)
    birthday: date = Field(..., description="Date of birth in format YYYY-MM-DD")
    description: Optional[str] = Field(None, min_length=3, max_length=250)
    emails: Optional[List[EmailSchema]] = None
    phones: Optional[List[PhoneSchema]] = None

    @validator('birthday', pre=True)
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(v, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Invalid date format. Date must be in YYYY-MM-DD format.')


class ContactUpdateSchema(ContactSchema):
    id: int


class ContactResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    birthday: date
    description: Optional[str]
    emails: Optional[List[EmailSchema]] = None
    phones: Optional[List[PhoneSchema]] = None

    class Config:
        from_attributes = True


class ContactCreate(ContactSchema):
    pass

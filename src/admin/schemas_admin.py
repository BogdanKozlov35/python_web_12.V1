from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str


class RoleResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True

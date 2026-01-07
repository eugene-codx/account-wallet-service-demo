from pydantic import UUID4, BaseModel


class User(BaseModel):
    id: UUID4
    username: str


class UserCreate(BaseModel):
    username: str
    password: str

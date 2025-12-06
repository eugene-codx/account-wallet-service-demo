from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str


class UserCreate(BaseModel):
    username: str
    password: str

from fastapi import FastAPI
from app.api.v1 import auth, users
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(users.router)


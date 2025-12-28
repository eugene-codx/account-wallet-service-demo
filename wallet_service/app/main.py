from fastapi import FastAPI
from app.api.v1 import wallet

app = FastAPI(title="wallet-service")
app.include_router(wallet.router)

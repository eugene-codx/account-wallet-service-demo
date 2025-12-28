from fastapi import APIRouter, Depends, Header, HTTPException
from app.core.security import verify_jwt
from app.schemas.wallet import WalletCreate, WalletResponse
from app.services.wallet_service import WalletService

router = APIRouter()


def get_current_user(authorization: str = Header(...)):
    """
    Достаём user_id из JWT, проверенного локально.
    """
    payload = verify_jwt(authorization)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id


@router.post("/wallet", response_model=WalletResponse)
async def create_wallet(
    data: WalletCreate,
    user_id: int = Depends(get_current_user)
):
    return await WalletService.create_wallet(user_id=user_id, data=data)


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(user_id: int = Depends(get_current_user)):
    return await WalletService.get_wallet(user_id=user_id)

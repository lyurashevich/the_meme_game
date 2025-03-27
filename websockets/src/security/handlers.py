from fastapi import APIRouter, Depends
from security.auth import get_current_user

router = APIRouter(prefix="/token")


@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)) -> dict:
    return {"message": f"hello {user}"}

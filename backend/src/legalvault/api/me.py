from pydantic import BaseModel

from legalvault.auth import AuthenticatedUser, get_current_user
from fastapi import APIRouter, Depends

router = APIRouter(tags=["auth"])


class MeResponse(BaseModel):
    user_id: str
    is_admin: bool


@router.get("/me", response_model=MeResponse)
def get_me(user: AuthenticatedUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(user_id=user.user_id, is_admin=user.is_admin)

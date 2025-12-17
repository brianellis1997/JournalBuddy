from fastapi import APIRouter

from app.api.deps import Database, CurrentUser
from app.crud.user import user_crud
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    user_in: UserUpdate,
    current_user: CurrentUser,
    db: Database,
):
    user = await user_crud.update(db, current_user, user_in)
    return user


@router.delete("/me")
async def delete_user_account(current_user: CurrentUser, db: Database):
    await user_crud.delete(db, current_user)
    return {"success": True}

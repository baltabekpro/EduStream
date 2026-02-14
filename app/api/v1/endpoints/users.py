"""
User profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User as UserModel
from app.schemas.swagger_schemas import User, UserUpdateRequest
from app.core.security import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])


def _swagger_user(current_user: UserModel) -> User:
    return User(
        id=current_user.id,
        email=current_user.email,
        firstName=current_user.first_name,
        lastName=current_user.last_name,
        avatar=current_user.avatar,
        role=current_user.role,
        settings=current_user.settings or {}
    )


@router.get("/me", response_model=User)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """Get current user profile."""
    return _swagger_user(current_user)


@router.patch("/me", response_model=User)
async def update_user_profile(
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """
    Обновление настроек профиля.
    
    Обновление имени, аватара и тумблеров уведомлений.
    """
    if update_data.firstName is not None:
        current_user.first_name = update_data.firstName
    
    if update_data.lastName is not None:
        current_user.last_name = update_data.lastName
    
    if update_data.settings is not None:
        current_user.settings = update_data.settings.dict()
    
    db.commit()
    db.refresh(current_user)

    return _swagger_user(current_user)


@router.put("/me")
async def update_user_profile_legacy(
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """Legacy profile update format used by tests/older clients."""
    if "first_name" in update_data:
        current_user.first_name = update_data.get("first_name")

    if "last_name" in update_data:
        current_user.last_name = update_data.get("last_name")

    if "bio" in update_data:
        settings = current_user.settings or {}
        settings["bio"] = update_data.get("bio")
        current_user.settings = settings

    db.commit()
    db.refresh(current_user)

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "bio": (current_user.settings or {}).get("bio"),
        "role": str(current_user.role.value) if hasattr(current_user.role, "value") else str(current_user.role)
    }


@router.post("/change-password")
async def change_password_legacy(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """Legacy password change endpoint."""
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="new_password must be at least 8 characters"
        )

    if not verify_password(current_password or "", current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_current_user_legacy(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """Legacy delete-account endpoint."""
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted"}

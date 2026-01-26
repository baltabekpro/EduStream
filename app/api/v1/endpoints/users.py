"""
User profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User as UserModel
from app.schemas.swagger_schemas import User, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=User)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_teacher)
):
    """Get current user profile."""
    return User(
        id=current_user.id,
        email=current_user.email,
        firstName=current_user.first_name,
        lastName=current_user.last_name,
        avatar=current_user.avatar,
        role=current_user.role,
        settings=current_user.settings or {}
    )


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
    
    return User(
        id=current_user.id,
        email=current_user.email,
        firstName=current_user.first_name,
        lastName=current_user.last_name,
        avatar=current_user.avatar,
        role=current_user.role,
        settings=current_user.settings or {}
    )

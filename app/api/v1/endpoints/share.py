"""
Public sharing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, PublicLink
from app.schemas.swagger_schemas import ShareConfig, ShareLink
from app.core.security import get_password_hash
import uuid
import secrets

router = APIRouter(prefix="/share", tags=["Shared"])


def generate_short_code() -> str:
    """Generate a short alphanumeric code for public links."""
    return secrets.token_urlsafe(8)


@router.post("/create", response_model=ShareLink, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    config: ShareConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Публичный шеринг.
    
    Создает короткую ссылку для доступа к тесту или результатам OCR 
    без логина (view-only).
    """
    # Generate unique short code
    short_code = generate_short_code()
    
    # Hash password if provided
    hashed_password = None
    if config.password:
        hashed_password = get_password_hash(config.password)
    
    # Create public link
    public_link = PublicLink(
        user_id=current_user.id,
        resource_id=config.resourceId,
        resource_type=config.resourceType.value,
        short_code=short_code,
        view_only=config.viewOnly if config.viewOnly is not None else True,
        allow_copy=config.allowCopy if config.allowCopy is not None else False,
        password=hashed_password
    )
    
    db.add(public_link)
    db.commit()
    db.refresh(public_link)
    
    # Construct URL
    base_url = "http://localhost:8000"  # TODO: Get from settings
    url = f"{base_url}/shared/{short_code}"
    
    return ShareLink(url=url)

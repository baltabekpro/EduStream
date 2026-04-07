from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is a teacher or admin."""
    role = str(getattr(current_user.role, "value", current_user.role)).lower()
    if role not in {"teacher", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can access this endpoint"
        )
    return current_user


async def get_language(
    accept_language: Optional[str] = Header(None)
) -> str:
    """
    Extract and validate language from Accept-Language header.
    
    Parses the Accept-Language header and returns the first supported language code.
    Supported languages: ru (Russian), kk (Kazakh), en (English).
    Defaults to 'ru' if header is missing or contains unsupported language.
    
    Args:
        accept_language: Accept-Language header value (e.g., "kk,ru;q=0.9,en;q=0.8")
    
    Returns:
        str: Validated language code ('ru', 'kk', or 'en')
    """
    supported_languages = {'ru', 'kk', 'en'}
    
    if accept_language:
        # Parse header: "kk,ru;q=0.9,en;q=0.8" -> extract first language code
        lang = accept_language.split(',')[0].split(';')[0].strip().lower()
        if lang in supported_languages:
            return lang
    
    return 'ru'  # Default to Russian

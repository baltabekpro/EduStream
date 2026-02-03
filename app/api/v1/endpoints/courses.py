"""
Courses endpoints - manage course metadata.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/courses", tags=["Courses"])


class Course(BaseModel):
    """Course metadata."""
    id: str
    title: str
    materialsCount: int


@router.get("/", response_model=List[Course])
async def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Список курсов пользователя.
    
    Возвращает уникальные course_id из materials с подсчетом материалов в каждом курсе.
    """
    # Get unique course_ids from materials
    courses_data = db.query(
        Material.course_id,
        func.count(Material.id).label('count')
    ).filter(
        Material.user_id == current_user.id,
        Material.course_id.isnot(None)
    ).group_by(Material.course_id).all()
    
    courses = [
        Course(
            id=course_id,
            title=course_id,  # Use course_id as title for now
            materialsCount=count
        )
        for course_id, count in courses_data
    ]
    
    return courses

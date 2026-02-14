"""
Courses endpoints - manage course metadata.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Course as CourseModel
from app.schemas.swagger_schemas import Course, CourseCreate, CourseUpdate
import uuid
from typing import List

router = APIRouter(prefix="/courses", tags=["Courses"])


def _to_course_response(db: Session, course: CourseModel) -> Course:
    count = db.query(func.count(Material.id)).filter(Material.course_id == str(course.id)).scalar() or 0
    return Course(
        id=str(course.id),
        title=course.title,
        description=course.description,
        color=course.color,
        icon=course.icon,
        materialsCount=int(count),
        createdAt=course.created_at.isoformat() if course.created_at else None,
        updatedAt=course.updated_at.isoformat() if course.updated_at else None,
    )


@router.get("/", response_model=List[Course])
async def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Список курсов пользователя.
    
    Возвращает уникальные course_id из materials с подсчетом материалов в каждом курсе.
    """
    courses = db.query(CourseModel).filter(
        CourseModel.user_id == current_user.id
    ).order_by(CourseModel.created_at.desc()).all()

    return [_to_course_response(db, course) for course in courses]


@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        course_uuid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course id")

    course = db.query(CourseModel).filter(
        CourseModel.id == course_uuid,
        CourseModel.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return _to_course_response(db, course)


@router.post("/", response_model=Course, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="title is required")

    course = CourseModel(
        user_id=current_user.id,
        title=title,
        description=payload.description,
        color=payload.color,
        icon=payload.icon,
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    return _to_course_response(db, course)


@router.put("/{course_id}", response_model=Course)
async def update_course(
    course_id: str,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        course_uuid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course id")

    course = db.query(CourseModel).filter(
        CourseModel.id == course_uuid,
        CourseModel.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if payload.title is not None:
        next_title = payload.title.strip()
        if not next_title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="title cannot be empty")
        course.title = next_title
    if payload.description is not None:
        course.description = payload.description
    if payload.color is not None:
        course.color = payload.color
    if payload.icon is not None:
        course.icon = payload.icon

    db.commit()
    db.refresh(course)
    return _to_course_response(db, course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    try:
        course_uuid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course id")

    course = db.query(CourseModel).filter(
        CourseModel.id == course_uuid,
        CourseModel.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    db.query(Material).filter(
        Material.user_id == current_user.id,
        Material.course_id == str(course.id)
    ).update({Material.course_id: None}, synchronize_session=False)

    db.delete(course)
    db.commit()
    return None

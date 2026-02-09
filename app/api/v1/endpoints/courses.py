"""
Courses endpoints - manage course metadata.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Course
from app.schemas.swagger_schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse
)
from typing import List
from uuid import UUID
import uuid as uuid_lib

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Список курсов пользователя с количеством материалов.
    """
    # Get all courses with material count
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    
    # Build response with material counts
    response = []
    for course in courses:
        material_count = db.query(func.count(Material.id)).filter(
            Material.course_id == course.id
        ).scalar() or 0
        
        response.append(CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            color=course.color,
            icon=course.icon,
            materialsCount=material_count,
            createdAt=course.created_at,
            updatedAt=course.updated_at
        ))
    
    return response


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Создание нового курса.
    """
    # Create new course
    new_course = Course(
        id=uuid_lib.uuid4(),
        user_id=current_user.id,
        title=course_data.title,
        description=course_data.description,
        color=course_data.color or "#3b82f6",
        icon=course_data.icon or "school"
    )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return CourseResponse(
        id=new_course.id,
        title=new_course.title,
        description=new_course.description,
        color=new_course.color,
        icon=new_course.icon,
        materialsCount=0,
        createdAt=new_course.created_at,
        updatedAt=new_course.updated_at
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Получение курса по ID.
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    material_count = db.query(func.count(Material.id)).filter(
        Material.course_id == course.id
    ).scalar() or 0
    
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        color=course.color,
        icon=course.icon,
        materialsCount=material_count,
        createdAt=course.created_at,
        updatedAt=course.updated_at
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Обновление курса.
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Update fields if provided
    if course_data.title is not None:
        course.title = course_data.title
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.color is not None:
        course.color = course_data.color
    if course_data.icon is not None:
        course.icon = course_data.icon
    
    db.commit()
    db.refresh(course)
    
    material_count = db.query(func.count(Material.id)).filter(
        Material.course_id == course.id
    ).scalar() or 0
    
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        color=course.color,
        icon=course.icon,
        materialsCount=material_count,
        createdAt=course.created_at,
        updatedAt=course.updated_at
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Удаление курса. Материалы курса станут без курса (course_id = NULL).
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Delete course (materials will have course_id set to NULL due to ondelete="SET NULL")
    db.delete(course)
    db.commit()
    
    return None


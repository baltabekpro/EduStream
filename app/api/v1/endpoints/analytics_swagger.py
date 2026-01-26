"""
Analytics endpoints - aligned with Swagger specification.
Visualization of class progress and individual student performance.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User
from app.schemas.swagger_schemas import (
    AnalyticsData,
    PerformanceItem,
    TopicItem,
    StudentMetric,
    StudentTrend
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/performance", response_model=AnalyticsData)
async def get_analytics_performance(
    courseId: str = Query(None, description="Course ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Полная аналитика.
    
    Данные для графиков, карты знаний и списка студентов.
    """
    # TODO: Implement actual analytics from DB
    # Mock data for now
    
    performance = [
        PerformanceItem(name="Понедельник", value=75),
        PerformanceItem(name="Вторник", value=82),
        PerformanceItem(name="Среда", value=78),
        PerformanceItem(name="Четверг", value=85),
        PerformanceItem(name="Пятница", value=88)
    ]
    
    topics = [
        TopicItem(name="Митохондрии", score=92, colorKey="green"),
        TopicItem(name="Фотосинтез", score=75, colorKey="yellow"),
        TopicItem(name="ДНК и РНК", score=88, colorKey="green"),
        TopicItem(name="Клеточная мембрана", score=65, colorKey="red"),
        TopicItem(name="Ядро клетки", score=80, colorKey="yellow")
    ]
    
    students = [
        StudentMetric(
            id=1,
            name="Иванов Петр",
            status="Отлично",
            progress=92.5,
            trend=StudentTrend.UP,
            color="green",
            avatar="/avatars/1.jpg"
        ),
        StudentMetric(
            id=2,
            name="Петрова Мария",
            status="Хорошо",
            progress=78.0,
            trend=StudentTrend.NEUTRAL,
            color="blue",
            avatar="/avatars/2.jpg"
        ),
        StudentMetric(
            id=3,
            name="Сидоров Алексей",
            status="Требует внимания",
            progress=62.5,
            trend=StudentTrend.DOWN,
            color="orange",
            avatar="/avatars/3.jpg"
        )
    ]
    
    return AnalyticsData(
        performance=performance,
        topics=topics,
        students=students
    )

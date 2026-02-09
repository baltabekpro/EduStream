"""
Dashboard endpoints.
Provides aggregated data for teacher's main screen.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User
from app.schemas.swagger_schemas import DashboardData, PieChartItem, NeedsReviewItem, RecentActivityItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardData)
async def get_dashboard_overview(
    courseId: Optional[str] = Query(None, description="Course ID to filter data (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Главный экран управления учителя.
    
    **Сценарий:** Учитель открывает приложение.
    **Зачем:** Получить мгновенную сводку: что требует проверки (OCR), 
    статистика класса, последние действия.
    Данные должны быть отфильтрованы по courseId.
    """
    # TODO: Implement actual data aggregation from DB
    # For now, return mock data matching Swagger schema
    
    pie_chart = [
        PieChartItem(name="Отлично", value=12, color="#10b981"),
        PieChartItem(name="Хорошо", value=25, color="#3b82f6"),
        PieChartItem(name="Удовлетв.", value=8, color="#f59e0b"),
        PieChartItem(name="Требует внимания", value=5, color="#ef4444")
    ]
    
    needs_review = [
        NeedsReviewItem(
            id="ocr-001",
            name="Самостоятельная работа №3",
            subject="Математика",
            img="/assets/math.jpg",
            type="ocr"
        )
    ]
    
    recent_activity = [
        RecentActivityItem(
            id=1,
            title="Тест по биологии",
            source="9А класс",
            time="2 часа назад",
            status="Готов",
            statusColor="green",
            type="quiz",
            action="Просмотреть"
        )
    ]
    
    return DashboardData(
        pieChart=pie_chart,
        needsReview=needs_review,
        recentActivity=recent_activity
    )

"""
Dashboard endpoints.
Provides aggregated data for teacher's main screen.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Quiz, StudentResult, OCRResult
from app.schemas.swagger_schemas import DashboardData, PieChartItem, NeedsReviewItem, RecentActivityItem, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _time_ago(dt: datetime | None) -> str:
    if not dt:
        return "только что"
    now = datetime.now(timezone.utc)
    source = dt
    if source.tzinfo is None:
        source = source.replace(tzinfo=timezone.utc)
    delta = now - source
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "только что"
    if minutes < 60:
        return f"{minutes} мин назад"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ч назад"
    days = hours // 24
    return f"{days} дн назад"


@router.get("/overview", response_model=DashboardData)
async def get_dashboard_overview(
    courseId: str = Query(..., description="Course ID to filter data"),
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
    materials = db.query(Material).filter(
        Material.user_id == current_user.id,
        Material.course_id == courseId
    ).all()
    material_ids = [m.id for m in materials]

    if material_ids:
        results = db.query(StudentResult).join(
            Quiz, StudentResult.quiz_id == Quiz.id
        ).filter(
            StudentResult.user_id == current_user.id,
            Quiz.material_id.in_(material_ids)
        ).all()
    else:
        results = []

    excellent = sum(1 for r in results if r.score >= 85)
    good = sum(1 for r in results if 70 <= r.score < 85)
    satisfactory = sum(1 for r in results if 50 <= r.score < 70)
    attention = sum(1 for r in results if r.score < 50)

    pie_chart = [
        PieChartItem(name="Отлично", value=excellent, color="#10b981"),
        PieChartItem(name="Хорошо", value=good, color="#3b82f6"),
        PieChartItem(name="Удовлетв.", value=satisfactory, color="#f59e0b"),
        PieChartItem(name="Требует внимания", value=attention, color="#ef4444")
    ]

    pending_ocr = db.query(OCRResult).filter(
        OCRResult.user_id == current_user.id,
        OCRResult.course_id == courseId,
        OCRResult.status.in_(["pending", "review"])
    ).order_by(OCRResult.created_at.desc()).limit(8).all()

    needs_review = [
        NeedsReviewItem(
            id=str(item.id),
            name=item.student_name or "Работа ученика",
            subject="Распознавание работы",
            img=item.image_url or "",
            type="ocr"
        )
        for item in pending_ocr
    ]

    recent_activity: list[RecentActivityItem] = []
    recent_materials = sorted(materials, key=lambda m: m.created_at or datetime.min, reverse=True)[:4]

    for index, mat in enumerate(recent_materials, start=1):
        recent_activity.append(
            RecentActivityItem(
                id=index,
                title=f"Материал: {mat.title}",
                source="Библиотека файлов",
                time=_time_ago(mat.created_at),
                status="Готов",
                statusColor="green" if str(mat.status).endswith("READY") or str(mat.status).endswith("ready") else "orange",
                type="ai",
                action="Открыть"
            )
        )

    recent_results = sorted(results, key=lambda r: r.submission_date or datetime.min, reverse=True)[:6]
    start_id = len(recent_activity) + 1
    for offset, res in enumerate(recent_results):
        recent_activity.append(
            RecentActivityItem(
                id=start_id + offset,
                title=f"Тест: {res.student_identifier}",
                source=f"Результат {int(res.score)}%",
                time=_time_ago(res.submission_date),
                status="Проверено",
                statusColor="green" if res.score >= 70 else "orange",
                type="quiz",
                action="Просмотреть"
            )
        )

    recent_activity = sorted(
        recent_activity,
        key=lambda item: item.id,
        reverse=False
    )[:10]

    unique_students = len({r.student_identifier.strip().lower() for r in results if r.student_identifier})
    average_score = round(sum(r.score for r in results) / len(results), 1) if results else 0.0

    return DashboardData(
        pieChart=pie_chart,
        needsReview=needs_review,
        recentActivity=recent_activity,
        stats=DashboardStats(
            averageScore=average_score,
            studentsCount=unique_students,
            submissionsCount=len(results),
            needsReviewCount=len(needs_review)
        )
    )

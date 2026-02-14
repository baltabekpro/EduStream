"""
Analytics endpoints - aligned with Swagger specification.
Visualization of class progress and individual student performance.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Quiz, StudentResult
from app.schemas.swagger_schemas import (
    AnalyticsData,
    PerformanceItem,
    TopicItem,
    StudentMetric,
    StudentTrend
)
from app.schemas.schemas import AnalyticsDashboardResponse, AnalyticsKnowledgeMapResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _normalize_student_key(name: str) -> str:
    return (name or "").strip().lower()


def _extract_diary_comments(settings: dict | None, course_id: str) -> dict[str, str]:
    if not isinstance(settings, dict):
        return {}
    comments_root = settings.get("studentDiaryComments")
    if not isinstance(comments_root, dict):
        return {}
    course_comments = comments_root.get(course_id)
    if not isinstance(course_comments, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in course_comments.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key.strip().lower()] = value
    return normalized


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard_legacy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    return AnalyticsDashboardResponse(
        stats={
            "total_materials": 0,
            "total_quizzes": 0,
            "total_student_results": 0,
            "average_score": 0.0,
        },
        recent_activities=[]
    )


@router.get("/knowledge-map", response_model=AnalyticsKnowledgeMapResponse)
async def get_knowledge_map_legacy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    return AnalyticsKnowledgeMapResponse(knowledge_map=[])


@router.get("/performance", response_model=AnalyticsData)
async def get_analytics_performance(
    courseId: str = Query(None, description="Course ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Полная аналитика по выбранному курсу на основе фактических результатов."""
    if not courseId:
        return AnalyticsData(performance=[], topics=[], students=[])

    materials = db.query(Material).filter(
        Material.user_id == current_user.id,
        Material.course_id == courseId
    ).all()
    material_ids = [m.id for m in materials]

    if not material_ids:
        return AnalyticsData(performance=[], topics=[], students=[])

    results = db.query(StudentResult).join(
        Quiz, StudentResult.quiz_id == Quiz.id
    ).filter(
        StudentResult.user_id == current_user.id,
        Quiz.material_id.in_(material_ids)
    ).order_by(StudentResult.submission_date.asc()).all()

    if not results:
        return AnalyticsData(performance=[], topics=[], students=[])

    today = datetime.utcnow().date()
    performance_items: list[PerformanceItem] = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_results = [r.score for r in results if r.submission_date and r.submission_date.date() == day]
        avg_day = round(sum(day_results) / len(day_results)) if day_results else 0
        performance_items.append(
            PerformanceItem(name=day.strftime("%d.%m"), value=avg_day)
        )

    topic_counter: Counter[str] = Counter()
    for res in results:
        weak_topics = res.weak_topics or []
        for topic in weak_topics:
            normalized = str(topic).strip()
            if normalized:
                topic_counter[normalized] += 1

    if topic_counter:
        max_count = max(topic_counter.values())
        topics = []
        for topic_name, count in topic_counter.most_common(8):
            score = max(0, min(100, int(round(100 - (count / max_count) * 45))))
            color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            topics.append(TopicItem(name=topic_name, score=score, colorKey=color))
    else:
        average = round(sum(r.score for r in results) / len(results))
        baseline_color = "green" if average >= 80 else "yellow" if average >= 60 else "red"
        topics = [
            TopicItem(name="Общая успеваемость", score=average, colorKey=baseline_color),
            TopicItem(name="Регулярность выполнения", score=min(100, len(results) * 5), colorKey="blue"),
        ]

    per_student: dict[str, list[StudentResult]] = defaultdict(list)
    for item in results:
        key = (item.student_identifier or "Ученик").strip()
        if not key:
            key = "Ученик"
        per_student[key].append(item)

    students: list[StudentMetric] = []
    for index, (student_name, student_items) in enumerate(per_student.items(), start=1):
        student_items = sorted(student_items, key=lambda r: r.submission_date or datetime.min)
        avg_score = sum(s.score for s in student_items) / len(student_items)

        recent_slice = student_items[-3:]
        previous_slice = student_items[-6:-3]
        recent_avg = sum(s.score for s in recent_slice) / len(recent_slice)
        previous_avg = sum(s.score for s in previous_slice) / len(previous_slice) if previous_slice else recent_avg

        if recent_avg > previous_avg + 2:
            trend = StudentTrend.UP
        elif recent_avg < previous_avg - 2:
            trend = StudentTrend.DOWN
        else:
            trend = StudentTrend.NEUTRAL

        attempts_count = len(student_items)
        is_regular = attempts_count >= 3

        if avg_score >= 85:
            status = "Отлично"
            color = "green"
        elif avg_score >= 70:
            status = "Хорошо"
            color = "blue"
        elif avg_score >= 50:
            status = "Удовлетворительно"
            color = "orange"
        else:
            status = "Требует внимания"
            color = "red"

        if is_regular and status == "Хорошо":
            status = "Постоянный: Хорошо"
        elif is_regular and status == "Отлично":
            status = "Постоянный: Отлично"

        students.append(
            StudentMetric(
                id=index,
                name=student_name,
                status=status,
                progress=round(avg_score, 1),
                trend=trend,
                color=color,
                avatar=f"https://api.dicebear.com/7.x/initials/svg?seed={student_name.replace(' ', '%20')}"
            )
        )

    students = sorted(students, key=lambda s: s.progress, reverse=True)

    return AnalyticsData(
        performance=performance_items,
        topics=topics,
        students=students
    )


@router.get("/student-journal")
async def get_student_journal(
    courseId: str = Query(..., description="Course ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    materials = db.query(Material).filter(
        Material.user_id == current_user.id,
        Material.course_id == courseId
    ).all()
    material_ids = [m.id for m in materials]

    if not material_ids:
        return {
            "courseId": courseId,
            "totalStudents": 0,
            "regularStudents": 0,
            "averageScore": 0,
            "students": []
        }

    material_map = {str(item.id): item.title for item in materials}

    rows = db.query(StudentResult, Quiz).join(
        Quiz, StudentResult.quiz_id == Quiz.id
    ).filter(
        StudentResult.user_id == current_user.id,
        Quiz.material_id.in_(material_ids)
    ).order_by(StudentResult.submission_date.desc()).all()

    if not rows:
        return {
            "courseId": courseId,
            "totalStudents": 0,
            "regularStudents": 0,
            "averageScore": 0,
            "students": []
        }

    comments_map = _extract_diary_comments(current_user.settings or {}, courseId)
    per_student: dict[str, list[dict]] = defaultdict(list)

    for result, quiz in rows:
        student_name = (result.student_identifier or "Ученик").strip() or "Ученик"
        student_key = _normalize_student_key(student_name)
        per_student[student_key].append({
            "resultId": str(result.id),
            "studentName": student_name,
            "score": int(result.score),
            "submittedAt": result.submission_date.isoformat() if result.submission_date else None,
            "quizId": str(quiz.id),
            "quizTitle": quiz.title or "Тест",
            "materialTitle": material_map.get(str(quiz.material_id), "Материал"),
            "weakTopics": [str(topic) for topic in (result.weak_topics or []) if topic]
        })

    students = []
    all_scores: list[int] = []
    regular_count = 0

    for student_key, history in per_student.items():
        ordered = sorted(
            history,
            key=lambda item: item.get("submittedAt") or "",
            reverse=True
        )
        attempts = len(ordered)
        scores = [int(item["score"]) for item in ordered]
        all_scores.extend(scores)

        avg_score = round(sum(scores) / attempts, 1) if attempts else 0
        last_score = scores[0] if scores else 0

        prev_window = scores[1:4]
        trend = "neutral"
        if prev_window:
            prev_avg = sum(prev_window) / len(prev_window)
            if last_score > prev_avg + 2:
                trend = "up"
            elif last_score < prev_avg - 2:
                trend = "down"

        is_regular = attempts >= 3
        if is_regular:
            regular_count += 1

        weak_topics = []
        for item in ordered[:5]:
            weak_topics.extend(item.get("weakTopics") or [])

        dedup_topics = []
        seen_topics = set()
        for topic in weak_topics:
            normalized_topic = topic.strip()
            if normalized_topic and normalized_topic.lower() not in seen_topics:
                seen_topics.add(normalized_topic.lower())
                dedup_topics.append(normalized_topic)

        students.append({
            "studentKey": student_key,
            "studentName": ordered[0]["studentName"],
            "attempts": attempts,
            "averageScore": avg_score,
            "lastScore": last_score,
            "regular": is_regular,
            "trend": trend,
            "teacherComment": comments_map.get(student_key, ""),
            "weakTopics": dedup_topics[:6],
            "history": ordered[:12]
        })

    students = sorted(students, key=lambda item: item["averageScore"], reverse=True)

    return {
        "courseId": courseId,
        "totalStudents": len(students),
        "regularStudents": regular_count,
        "averageScore": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "students": students
    }


@router.patch("/student-journal/comment")
async def update_student_journal_comment(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    course_id = str(payload.get("courseId") or "").strip()
    student_name = str(payload.get("studentName") or "").strip()
    comment = str(payload.get("comment") or "").strip()

    if not course_id:
        raise HTTPException(status_code=422, detail="courseId is required")
    if not student_name:
        raise HTTPException(status_code=422, detail="studentName is required")

    settings = dict(current_user.settings) if isinstance(current_user.settings, dict) else {}
    comments_root_raw = settings.get("studentDiaryComments")
    comments_root = dict(comments_root_raw) if isinstance(comments_root_raw, dict) else {}

    course_comments_raw = comments_root.get(course_id)
    course_comments = dict(course_comments_raw) if isinstance(course_comments_raw, dict) else {}

    student_key = _normalize_student_key(student_name)
    if comment:
        course_comments[student_key] = comment
    else:
        course_comments.pop(student_key, None)

    comments_root[course_id] = course_comments
    settings["studentDiaryComments"] = comments_root
    current_user.settings = settings

    db.commit()

    return {
        "courseId": course_id,
        "studentName": student_name,
        "comment": course_comments.get(student_key, "")
    }

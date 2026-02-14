"""
Public sharing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, PublicLink, Quiz as QuizModel, Material, StudentResult
from app.schemas.swagger_schemas import ShareConfig, ShareLink
from app.core.security import get_password_hash, verify_password
import uuid
import secrets
from datetime import datetime

router = APIRouter(prefix="/share", tags=["Shared"])


def generate_short_code() -> str:
    """Generate a short alphanumeric code for public links."""
    return secrets.token_urlsafe(8)


@router.post("/create", response_model=ShareLink, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    config: ShareConfig,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Публичный шеринг.
    
    Создает короткую ссылку для доступа к тесту или результатам OCR 
    без логина (view-only).
    """
    # Ensure teacher can only share own resources
    if config.resourceType.value == "quiz":
        try:
            quiz_uuid = uuid.UUID(str(config.resourceId))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid quiz id"
            )

        quiz = db.query(QuizModel).join(Material, QuizModel.material_id == Material.id).filter(
            QuizModel.id == quiz_uuid,
            Material.user_id == current_user.id
        ).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )

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
        password=hashed_password,
        expires_at=config.expiresAt if hasattr(config, 'expiresAt') else None
    )
    
    db.add(public_link)
    db.commit()
    db.refresh(public_link)
    
    # Construct URL
    # Build public frontend URL from current host
    if request.url.hostname in ["localhost", "127.0.0.1"]:
        base_url = f"{request.url.scheme}://{request.url.hostname}:3000"
    else:
        base_url = f"{request.url.scheme}://{request.url.hostname}"
    url = f"{base_url}/#/shared/{short_code}"
    
    return ShareLink(url=url)


@router.get("/{short_code}")
async def get_shared_resource(
    short_code: str,
    password: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Public endpoint: get shared resource by short code."""
    link = db.query(PublicLink).filter(PublicLink.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Shared link has expired")

    if link.password:
        if not password or not verify_password(password, link.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password required or invalid")

    if link.resource_type != "quiz":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported shared resource")

    try:
        quiz_uuid = uuid.UUID(str(link.resource_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shared resource id")

    quiz = db.query(QuizModel).filter(QuizModel.id == quiz_uuid).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    material = db.query(Material).filter(Material.id == quiz.material_id).first()

    # Public payload: no correct answers
    questions = []
    for q in (quiz.questions or []):
        if not isinstance(q, dict):
            continue
        questions.append({
            "id": q.get("id") or str(uuid.uuid4()),
            "type": q.get("type", "mcq"),
            "text": q.get("text") or q.get("question", ""),
            "options": q.get("options") or [],
        })

    return {
        "resourceType": "quiz",
        "shortCode": short_code,
        "viewOnly": link.view_only,
        "allowCopy": link.allow_copy,
        "title": material.title if material else "Quiz",
        "quizId": str(quiz.id),
        "questions": questions
    }


@router.post("/{short_code}/submit")
async def submit_shared_quiz(
    short_code: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Public endpoint: submit shared quiz answers and return score."""
    link = db.query(PublicLink).filter(PublicLink.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Shared link has expired")

    if link.resource_type != "quiz":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported shared resource")

    try:
        quiz_uuid = uuid.UUID(str(link.resource_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shared resource id")

    quiz = db.query(QuizModel).filter(QuizModel.id == quiz_uuid).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    answers = payload.get("answers") or {}
    student_name = (payload.get("studentName") or "Student").strip()[:255]

    questions = [q for q in (quiz.questions or []) if isinstance(q, dict)]
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz has no questions")

    total = len(questions)
    correct = 0
    details = []

    for q in questions:
        qid = str(q.get("id") or "")
        correct_answer = str(q.get("correctAnswer") or q.get("correct_answer") or "").strip()
        user_answer = str(answers.get(qid, "")).strip()

        is_correct = user_answer.lower() == correct_answer.lower() if correct_answer else False
        if is_correct:
            correct += 1

        details.append({
            "questionId": qid,
            "userAnswer": user_answer,
            "correctAnswer": correct_answer,
            "isCorrect": is_correct
        })

    score = round((correct / total) * 100) if total > 0 else 0

    # Persist result for teacher analytics
    result = StudentResult(
        user_id=link.user_id,
        student_identifier=student_name,
        quiz_id=quiz.id,
        score=score,
        weak_topics=[]
    )
    db.add(result)
    db.commit()

    return {
        "quizId": str(quiz.id),
        "studentName": student_name,
        "score": score,
        "correct": correct,
        "total": total,
        "details": details
    }

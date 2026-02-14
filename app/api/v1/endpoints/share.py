"""
Public sharing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi import Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_teacher
from app.models.models import User, PublicLink, Quiz as QuizModel, Material, StudentResult, OCRResult
from app.schemas.swagger_schemas import ShareConfig, ShareLink
from app.core.security import get_password_hash, verify_password
from app.services.file_processor import file_processor
import uuid
import secrets
import string
import re
from datetime import datetime
import os

router = APIRouter(prefix="/share", tags=["Shared"])


def generate_short_code() -> str:
    """Generate a short alphanumeric code for public links."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def validate_short_code_or_400(short_code: str) -> str:
    code = (short_code or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,32}", code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid short code format")
    return code


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
    elif config.resourceType.value == "material":
        try:
            material_uuid = uuid.UUID(str(config.resourceId))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid material id"
            )

        material = db.query(Material).filter(
            Material.id == material_uuid,
            Material.user_id == current_user.id
        ).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )

    # Generate unique short code
    short_code = None
    for _ in range(10):
        candidate = generate_short_code()
        exists = db.query(PublicLink).filter(PublicLink.short_code == candidate).first()
        if not exists:
            short_code = candidate
            break
    if not short_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique share code"
        )
    
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
    frontend_base_url = (settings.FRONTEND_BASE_URL or "").strip().rstrip("/")
    if frontend_base_url:
        base_url = frontend_base_url
    elif request.url.hostname in ["localhost", "127.0.0.1"]:
        base_url = f"{request.url.scheme}://{request.url.hostname}:3000"
    else:
        base_url = f"{request.url.scheme}://{request.url.hostname}"
    url = f"{base_url}/#/shared/{short_code}"
    
    return ShareLink(url=url)


@router.get("/quiz-results")
async def get_teacher_quiz_results(
    quizId: str | None = Query(default=None),
    courseId: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    query = db.query(StudentResult, QuizModel, Material).join(
        QuizModel, StudentResult.quiz_id == QuizModel.id
    ).join(
        Material, QuizModel.material_id == Material.id
    ).filter(
        StudentResult.user_id == current_user.id
    )

    if quizId:
        try:
            quiz_uuid = uuid.UUID(str(quizId))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quiz id")
        query = query.filter(StudentResult.quiz_id == quiz_uuid)

    if courseId:
        query = query.filter(Material.course_id == courseId)

    rows = query.order_by(StudentResult.submission_date.desc()).all()

    items = []
    for result, quiz, material in rows:
        total_questions = len(quiz.questions or []) if isinstance(quiz.questions, list) else 0
        items.append({
            "resultId": str(result.id),
            "quizId": str(quiz.id),
            "materialId": str(material.id),
            "materialTitle": material.title,
            "studentName": result.student_identifier,
            "score": int(result.score),
            "submittedAt": result.submission_date.isoformat(),
            "totalQuestions": total_questions,
        })

    return items


@router.get("/{short_code}")
async def get_shared_resource(
    short_code: str,
    password: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Public endpoint: get shared resource by short code."""
    short_code = validate_short_code_or_400(short_code)
    link = db.query(PublicLink).filter(PublicLink.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Shared link has expired")

    if link.password:
        if not password or not verify_password(password, link.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password required or invalid")

    if link.resource_type == "quiz":
        try:
            quiz_uuid = uuid.UUID(str(link.resource_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shared resource id")

        quiz = db.query(QuizModel).filter(QuizModel.id == quiz_uuid).first()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        material = db.query(Material).filter(Material.id == quiz.material_id).first()

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
            "title": quiz.title or (material.title if material else "Quiz"),
            "quizId": str(quiz.id),
            "questions": questions
        }

    if link.resource_type == "material":
        try:
            material_uuid = uuid.UUID(str(link.resource_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shared resource id")

        material = db.query(Material).filter(Material.id == material_uuid).first()
        if not material:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

        return {
            "resourceType": "material",
            "shortCode": short_code,
            "viewOnly": link.view_only,
            "allowCopy": link.allow_copy,
            "title": f"Задание: {material.title}",
            "materialId": str(material.id),
            "description": (material.summary or material.content or "").strip()[:1200],
            "acceptUploads": True,
            "acceptTextResponse": True,
        }

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported shared resource")


@router.post("/{short_code}/submit")
async def submit_shared_quiz(
    short_code: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Public endpoint: submit shared quiz answers and return score."""
    short_code = validate_short_code_or_400(short_code)
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
    weak_topics: list[str] = []

    for q in questions:
        qid = str(q.get("id") or "")
        correct_answer = str(q.get("correctAnswer") or q.get("correct_answer") or "").strip()
        user_answer = str(answers.get(qid, "")).strip()

        is_correct = user_answer.lower() == correct_answer.lower() if correct_answer else False
        if is_correct:
            correct += 1
        else:
            topic_candidate = str(q.get("topic") or q.get("text") or "").strip()
            if topic_candidate:
                weak_topics.append(topic_candidate[:80])

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
        weak_topics=weak_topics
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


@router.post("/{short_code}/upload")
async def upload_assignment_file(
    short_code: str,
    studentName: str = Form(...),
    responseText: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db)
):
    """Public endpoint: upload completed assignment document for material shares."""
    short_code = validate_short_code_or_400(short_code)
    link = db.query(PublicLink).filter(PublicLink.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Shared link has expired")

    if link.resource_type != "material":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploads are available only for assignment links")

    try:
        material_uuid = uuid.UUID(str(link.resource_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shared resource id")

    material = db.query(Material).filter(Material.id == material_uuid).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    student_name = (studentName or "Student").strip()[:255]
    response_text = (responseText or "").strip()
    allowed_extensions = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    if not file and not response_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attach a file and/or provide text response")

    saved_path = "text_submission"
    if file is not None:
        file_name = file.filename or ""
        extension = os.path.splitext(file_name)[1].lower()
        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Allowed: pdf, docx, txt, and images"
            )

        try:
            saved_path = await file_processor.save_file(file, str(uuid.uuid4()))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    response_regions = []
    if response_text:
        response_regions.append({
            "id": "text-response",
            "label": "Ответ ученика",
            "original": "",
            "ocrText": response_text,
            "confidence": "High",
            "match": None,
        })

    submission = OCRResult(
        user_id=link.user_id,
        student_name=student_name,
        student_accuracy=None,
        image_url=saved_path,
        questions=response_regions,
        status="pending",
        manual_score=None,
        course_id=material.course_id
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "submissionId": str(submission.id),
        "status": submission.status,
        "studentName": student_name,
        "message": "Ответ отправлен учителю"
    }



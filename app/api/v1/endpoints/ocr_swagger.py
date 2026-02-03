"""
OCR endpoints - aligned with Swagger specification.
Pipeline: Upload -> Recognition -> Grading.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, OCRResult
from app.schemas.swagger_schemas import (
    StudentResult,
    StudentInfo,
    OCRRegion,
    OCRManualCorrection,
    BatchApproveRequest
)
import uuid

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/results/{id}", response_model=StudentResult)
async def get_ocr_result(
    id: str = Path(..., description="OCR result ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Детали проверки OCR.
    
    Возвращает данные работы студента с распознанным текстом и оценками.
    """
    ocr_result = db.query(OCRResult).filter(
        OCRResult.id == id,
        OCRResult.user_id == current_user.id
    ).first()
    
    if not ocr_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR result not found"
        )
    
    # Convert to response format
    questions = [OCRRegion(**q) for q in ocr_result.questions]
    
    return StudentResult(
        id=ocr_result.id,
        student=StudentInfo(
            name=ocr_result.student_name,
            accuracy=ocr_result.student_accuracy or 0
        ),
        image=ocr_result.image_url,
        questions=questions
    )


@router.patch("/results/{id}")
async def update_ocr_result(
    id: str = Path(..., description="OCR result ID"),
    correction: OCRManualCorrection = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Ручная коррекция OCR результатов.
    
    **Сценарий:** Учитель исправляет ошибку распознавания текста или 
    меняет оценку вручную.
    
    Это действие должно пересчитывать статистику студента в Analytics.
    """
    ocr_result = db.query(OCRResult).filter(
        OCRResult.id == id,
        OCRResult.user_id == current_user.id
    ).first()
    
    if not ocr_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR result not found"
        )
    
    # Update manual score
    if correction.manualScore is not None:
        ocr_result.manual_score = correction.manualScore
    
    # Update corrected text
    if correction.correctedText:
        questions = ocr_result.questions or []
        for question in questions:
            region_id = question.get("id")
            if region_id in correction.correctedText:
                question["ocrText"] = correction.correctedText[region_id]
        
        ocr_result.questions = questions
    
    # Recalculate student accuracy if needed
    # TODO: Implement analytics recalculation
    
    db.commit()
    
    return {"status": "saved"}


@router.post("/batch-approve")
async def batch_approve_ocr(
    request: BatchApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Пакетное подтверждение OCR результатов.
    
    **Сценарий:** Dashboard -> Кнопка "Подтвердить все" в очереди OCR.
    
    Принимает массив ID работ. Переводит их статус в "Graded" и обновляет журнал.
    
    **Важно:** Если среди работ есть Low Confidence регионы, бэкенд должен 
    либо принять их как есть, либо вернуть предупреждение.
    
    **Ответы:**
    - 200: Успешно подтверждено
    - 207: Multi-Status (часть подтверждена, часть с ошибками)
    """
    results = []
    errors = []
    
    for ocr_id in request.ids:
        ocr_result = db.query(OCRResult).filter(
            OCRResult.id == ocr_id,
            OCRResult.user_id == current_user.id
        ).first()
        
        if not ocr_result:
            errors.append({
                "id": ocr_id,
                "error": "Not found"
            })
            continue
        
        # Check for low confidence regions
        low_confidence_count = 0
        if ocr_result.questions:
            for question in ocr_result.questions:
                if question.get("confidence") == "Low":
                    low_confidence_count += 1
        
        # Update status to graded
        ocr_result.status = "graded"
        results.append({
            "id": ocr_id,
            "status": "approved",
            "lowConfidenceWarnings": low_confidence_count
        })
    
    db.commit()
    
    # Return appropriate status code
    if errors:
        return {
            "status": "partial",
            "approved": results,
            "errors": errors
        }
    
    return {
        "status": "success",
        "approved": results
    }


@router.get("/queue")
async def get_ocr_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Получить очередь OCR задач.
    
    Возвращает список ожидающих и обрабатываемых OCR задач.
    """
    # Get pending OCR results
    ocr_results = db.query(OCRResult).filter(
        OCRResult.user_id == current_user.id,
        OCRResult.status.in_(["processing", "pending"])
    ).all()
    
    queue_items = [
        {
            "id": str(result.id),
            "filename": result.image_url or "unknown",
            "status": result.status,
            "created_at": result.created_at.isoformat()
        }
        for result in ocr_results
    ]
    
    return {
        "queue": queue_items,
        "total": len(queue_items)
    }

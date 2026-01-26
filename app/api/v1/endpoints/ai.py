from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Quiz
from app.schemas.schemas import (
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizQuestion
)
from app.services.ai_service import ai_service
import uuid

router = APIRouter(prefix="/ai", tags=["AI Generation"])


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    request: GenerateSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Generate summary and glossary from material using AI.
    """
    # Get material
    material = db.query(Material).filter(
        Material.id == request.material_id,
        Material.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    if not material.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material has no text content"
        )
    
    try:
        # Generate summary using AI
        result = await ai_service.generate_summary(material.raw_text)
        
        if not result.get("is_educational", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The text does not contain educational material"
            )
        
        # Update material with summary and glossary
        material.summary = result.get("summary")
        material.glossary = result.get("glossary")
        
        db.commit()
        db.refresh(material)
        
        return {
            "material_id": material.id,
            "summary": material.summary,
            "glossary": material.glossary
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Generate quiz questions from material using AI.
    """
    # Get material
    material = db.query(Material).filter(
        Material.id == request.material_id,
        Material.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    if not material.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material has no text content"
        )
    
    try:
        # Generate quiz using AI
        questions = await ai_service.generate_quiz(
            material.raw_text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        
        # Create quiz record
        quiz = Quiz(
            material_id=material.id,
            questions=questions
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Convert to response format
        quiz_questions = [QuizQuestion(**q) for q in questions]
        
        return {
            "quiz_id": quiz.id,
            "material_id": material.id,
            "questions": quiz_questions
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

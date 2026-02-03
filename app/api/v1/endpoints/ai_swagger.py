"""
AI Engine endpoints - aligned with Swagger specification.
Orchestration of LLM requests, RAG context management, and prompt engineering.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Quiz as QuizModel, AISession
from app.schemas.swagger_schemas import (
    QuizTemplate,
    QuizConfig,
    Quiz,
    Question,
    ChatRequest,
    SmartActionRequest,
    SmartActionResponse,
    RegenerateBlockRequest,
    AISessionInfo,
    QuestionType
)
from app.services.ai_service import ai_service
from datetime import datetime
import uuid

router = APIRouter(prefix="/ai", tags=["AI Engine"])


@router.get("/templates", response_model=list[QuizTemplate])
async def get_quiz_templates(
    current_user: User = Depends(get_current_teacher)
):
    """
    Галерея шаблонов тестов.
    
    **Сценарий:** Dashboard -> Галерея шаблонов.
    Возвращает список пресетов (например, "Пятиминутка", "Итоговая"), 
    чтобы учитель не настраивал конфиг с нуля.
    """
    # Mock templates - in production, these would come from DB
    templates = [
        QuizTemplate(
            id=1,
            title="Входное тестирование",
            desc="15 вопросов для оценки базовых знаний",
            icon="login",
            color="blue",
            config=QuizConfig(
                materialId=uuid.uuid4(),
                difficulty="medium",
                count=15,
                type=QuestionType.MCQ
            )
        ),
        QuizTemplate(
            id=2,
            title="Пятиминутка",
            desc="Быстрая проверка усвоения материала",
            icon="clock",
            color="green",
            config=QuizConfig(
                materialId=uuid.uuid4(),
                difficulty="easy",
                count=5,
                type=QuestionType.MCQ
            )
        ),
        QuizTemplate(
            id=3,
            title="Итоговая работа",
            desc="Комплексная проверка знаний по теме",
            icon="graduation-cap",
            color="purple",
            config=QuizConfig(
                materialId=uuid.uuid4(),
                difficulty="hard",
                count=25,
                type=QuestionType.MCQ
            )
        )
    ]
    
    return templates


@router.post("/chat")
async def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    RAG Chat - основной эндпоинт для чата в AI Workspace.
    
    Использует materialId для извлечения контекста (Retrieval Augmented Generation).
    
    **Возможные ошибки:**
    - 429: Rate Limit Exceeded (слишком много запросов)
    - 503: LLM Service Unavailable
    """
    # TODO: Implement rate limiting
    # TODO: Implement RAG context retrieval
    
    context = ""
    if request.materialId:
        # Validate UUID format
        try:
            material_uuid = uuid.UUID(request.materialId) if isinstance(request.materialId, str) else request.materialId
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid materialId format: {request.materialId}"
            )
        
        material = db.query(Material).filter(
            Material.id == material_uuid,
            Material.user_id == current_user.id
        ).first()
        
        if material and material.content:
            context = material.content[:2000]  # Limit context size
    
    try:
        # Call AI service with context
        response = await ai_service.chat_with_context(
            message=request.message,
            context=context
        )
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Service Unavailable"
        )


@router.post("/smart-action", response_model=SmartActionResponse)
async def smart_action(
    request: SmartActionRequest,
    current_user: User = Depends(get_current_teacher)
):
    """
    Контекстные действия (Smart Selection).
    
    **Сценарий:** Учитель выделяет текст в документе -> всплывает меню -> 
    выбирает "Упростить" или "Объяснить".
    
    Легковесный эндпоинт для быстрых трансформаций текста без сохранения 
    в историю чата.
    """
    try:
        result = await ai_service.perform_smart_action(
            text=request.text,
            action=request.action.value,
            context=request.context
        )
        
        return SmartActionResponse(result=result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate-quiz", response_model=Quiz)
async def generate_quiz(
    config: QuizConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Генератор тестов.
    
    **Сценарий:** AI Workspace -> Tab "Test Builder".
    Генерирует массив вопросов на основе материала.
    
    **Важно:** Ответ должен быть строго структурирован JSON.
    
    **Ошибки:**
    - 422: Невалидная конфигурация (например, count > 50)
    - 504: Timeout (генерация заняла слишком много времени)
    """
    # Validate count
    if config.count > 50 or config.count < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="count must be between 1 and 50"
        )
    
    # Validate materialId UUID format
    try:
        material_uuid = uuid.UUID(str(config.materialId)) if not isinstance(config.materialId, uuid.UUID) else config.materialId
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid materialId format: {config.materialId}"
        )
    
    # Get material
    material = db.query(Material).filter(
        Material.id == material_uuid,
        Material.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    if not material.content and not material.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material has no text content"
        )
    
    content = material.content or material.raw_text
    
    try:
        # Generate quiz using AI with difficulty-aware prompts
        questions_data = await ai_service.generate_quiz_advanced(
            text=content,
            count=config.count,
            difficulty=config.difficulty.value,
            question_type=config.type.value
        )
        
        # Create quiz record
        quiz = QuizModel(
            material_id=material.id,
            questions=questions_data
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Convert to response format
        questions = [
            Question(
                id=uuid.uuid4(),
                type=QuestionType(q.get("type", config.type.value)),
                text=q["text"],
                options=q.get("options"),
                correctAnswer=q["correctAnswer"],
                explanation=q.get("explanation")
            )
            for q in questions_data
        ]
        
        return Quiz(
            id=quiz.id,
            materialId=material.id,
            questions=questions,
            createdAt=quiz.created_at
        )
        
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Quiz generation timeout"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/regenerate-block", response_model=Question)
async def regenerate_block(
    request: RegenerateBlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Точечная перегенерация.
    
    **Сценарий:** Учителю не понравился один конкретный вопрос в тесте.
    Вместо пересоздания всего теста, мы обновляем только один блок, 
    сохраняя общий контекст.
    """
    try:
        # TODO: Load context from AISession
        # For now, regenerate based on current text and instruction
        
        regenerated = await ai_service.regenerate_question(
            current_text=request.currentText,
            instruction=request.instruction or "Улучши этот вопрос"
        )
        
        return Question(
            id=uuid.uuid4(),
            type=QuestionType.MCQ,  # TODO: Detect from regenerated
            text=regenerated.get("text", ""),
            options=regenerated.get("options"),
            correctAnswer=regenerated.get("correctAnswer", ""),
            explanation=regenerated.get("explanation")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions", response_model=list[AISessionInfo])
async def get_ai_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    История чатов.
    
    Для Sidebar в AI Workspace.
    """
    sessions = db.query(AISession).filter(
        AISession.user_id == current_user.id
    ).order_by(AISession.date.desc()).limit(20).all()
    
    return [
        AISessionInfo(
            id=session.id,
            title=session.title,
            date=session.date.isoformat(),
            docId=str(session.doc_id) if session.doc_id else None
        )
        for session in sessions
    ]

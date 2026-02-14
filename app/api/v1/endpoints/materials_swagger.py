"""
Materials endpoints - aligned with Swagger specification.
Managing educational materials knowledge base (PDF, images) for RAG.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material as MaterialModel, MaterialStatus
from app.schemas.swagger_schemas import Material, MaterialUploadResponse
from app.services.file_processor import file_processor
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.get("/", response_model=list[Material])
async def list_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Список файлов.
    
    Возвращает все материалы пользователя.
    """
    materials = db.query(MaterialModel).filter(
        MaterialModel.user_id == current_user.id
    ).order_by(MaterialModel.created_at.desc()).all()
    
    return [
        Material(
            id=str(m.id),
            title=m.title,
            content=m.content or m.raw_text,
            uploadDate=m.upload_date.isoformat() if m.upload_date else m.created_at.isoformat(),
            status=m.status
        )
        for m in materials
    ]


@router.post("/", response_model=MaterialUploadResponse, status_code=status.HTTP_202_ACCEPTED)
@router.post("/upload", response_model=MaterialUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_material(
    file: UploadFile = File(...),
    courseId: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Загрузка материалов (Upload).
    
    Загрузка PDF или изображений.
    Запускает асинхронный пайплайн: OCR -> Text Extraction -> Vector Embedding (для RAG).
    
    **Статус:** 202 Accepted (Processing started)
    """
    # Create material with processing status
    material = MaterialModel(
        user_id=current_user.id,
        title=file.filename,
        status=MaterialStatus.PROCESSING,
        course_id=courseId
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    # Start async processing
    # TODO: Implement background task for text extraction and vector embedding
    try:
        logger.info(f"Processing material {material.id}: {file.filename}")
        
        # Save file
        file_path = await file_processor.save_file(file, str(material.id))
        material.file_url = file_path
        logger.info(f"File saved to {file_path}")
        
        # Extract text
        text = await file_processor.extract_text(file_path)
        material.content = text
        material.raw_text = text
        material.status = MaterialStatus.READY
        
        logger.info(f"Material {material.id} processed successfully. Extracted {len(text)} characters")
        
        db.commit()
        db.refresh(material)
        
    except Exception as e:
        error_msg = f"Error processing material: {str(e)}"
        logger.error(f"Material {material.id}: {error_msg}")
        material.status = MaterialStatus.ERROR
        db.commit()
        
        # Return error details for debugging
        return MaterialUploadResponse(
            id=material.id,
            status=MaterialStatus.ERROR,
            message=error_msg
        )
    
    return MaterialUploadResponse(
        id=material.id,
        status=material.status,
        message=f"Material processed successfully. Extracted {len(material.content or '')} characters"
    )


@router.get("/{id}", response_model=Material)
async def get_material(
    id: str = Path(..., description="Material ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Контент документа.
    
    Возвращает сырой текст документа для отображения в левой панели AI Workspace.
    """
    # Validate UUID format
    try:
        material_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {id}"
        )
    
    material = db.query(MaterialModel).filter(
        MaterialModel.id == material_uuid,
        MaterialModel.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    return Material(
        id=str(material.id),
        title=material.title,
        content=material.content or material.raw_text,
        uploadDate=material.upload_date.isoformat() if material.upload_date else material.created_at.isoformat(),
        status=material.status
    )

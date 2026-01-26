from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material
from app.schemas.schemas import MaterialResponse
from app.services.file_processor import process_uploaded_file
from typing import List
import uuid

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Upload educational material (PDF/DOCX).
    Extracts text and saves to database.
    """
    try:
        # Process file
        file_path, extracted_text = await process_uploaded_file(file)
        
        # Create material record
        material = Material(
            user_id=current_user.id,
            title=file.filename,
            raw_text=extracted_text,
            file_url=file_path
        )
        
        db.add(material)
        db.commit()
        db.refresh(material)
        
        return material
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload material: {str(e)}"
        )


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get material by ID."""
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    return material


@router.get("/", response_model=List[MaterialResponse])
async def list_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """List all materials for current user."""
    materials = db.query(Material).filter(
        Material.user_id == current_user.id
    ).all()
    
    return materials

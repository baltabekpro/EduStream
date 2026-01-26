from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User
from app.schemas.schemas import OCRRecognizeResponse
from app.services.ocr_service import ocr_service
import os
import uuid
from app.core.config import settings

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/recognize", response_model=OCRRecognizeResponse)
async def recognize_text(
    file: UploadFile = File(...),
    reference_answer: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Recognize text from image using OCR.
    Optionally compare with reference answer.
    """
    try:
        # Validate file type
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are supported"
            )
        
        # Save uploaded image temporarily
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_path = os.path.join(upload_dir, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Recognize text
        recognized_text = await ocr_service.recognize_text(temp_path)
        
        # Check answer if reference provided
        errors = None
        if reference_answer:
            errors = await ocr_service.check_answer(recognized_text, reference_answer)
        
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass
        
        return {
            "text": recognized_text,
            "errors": errors
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

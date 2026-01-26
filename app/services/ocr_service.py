from typing import Optional, List
import os
from PIL import Image
import pytesseract
from app.core.config import settings


class OCRService:
    """Service for OCR text recognition."""
    
    async def recognize_text(self, image_path: str) -> str:
        """
        Recognize text from image using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Recognized text
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR with Russian and English languages
            text = pytesseract.image_to_string(image, lang='rus+eng')
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to recognize text from image: {str(e)}")
    
    async def check_answer(
        self, 
        recognized_text: str, 
        reference_answer: str
    ) -> List[str]:
        """
        Check recognized answer against reference answer.
        
        Args:
            recognized_text: Text recognized from student's work
            reference_answer: Reference correct answer
            
        Returns:
            List of errors found
        """
        # Simple implementation - can be enhanced with AI
        errors = []
        
        # Basic checks
        if not recognized_text:
            errors.append("No text recognized")
            return errors
        
        # Normalize texts for comparison
        recognized_lower = recognized_text.lower().strip()
        reference_lower = reference_answer.lower().strip()
        
        if recognized_lower != reference_lower:
            errors.append("Answer does not match reference")
        
        return errors


# Global instance
ocr_service = OCRService()

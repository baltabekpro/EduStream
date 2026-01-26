import os
from typing import Optional
from PyPDF2 import PdfReader
from docx import Document
from fastapi import UploadFile
from app.core.config import settings


class FileProcessor:
    """Service for file processing and text extraction."""
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    async def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    async def save_file(self, upload_file: UploadFile, material_id: str) -> str:
        """Save uploaded file to disk."""
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create unique filename
        file_extension = os.path.splitext(upload_file.filename)[1]
        destination = os.path.join(upload_dir, f"{material_id}{file_extension}")
        
        with open(destination, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        
        return destination
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from file based on extension."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == ".pdf":
            return await self.extract_text_from_pdf(file_path)
        elif file_extension == ".docx":
            return await self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


# Legacy functions for backward compatibility
async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


async def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to disk."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    return destination


async def process_uploaded_file(upload_file: UploadFile) -> tuple[str, str]:
    """
    Process uploaded file and extract text.
    Returns tuple of (file_path, extracted_text).
    """
    # Validate file extension
    file_extension = os.path.splitext(upload_file.filename)[1].lower()
    if file_extension not in [".pdf", ".docx"]:
        raise ValueError("Only PDF and DOCX files are supported")
    
    # Save file
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, upload_file.filename)
    await save_upload_file(upload_file, file_path)
    
    # Extract text
    if file_extension == ".pdf":
        text = await extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        text = await extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")
    
    return file_path, text


# Global instance
file_processor = FileProcessor()

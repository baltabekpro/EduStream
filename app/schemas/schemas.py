from pydantic import BaseModel, EmailStr, Field, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    TEACHER = "teacher"
    ADMIN = "admin"
    STUDENT = "student"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    OPEN = "Open"


# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters)")
    name: Optional[str] = Field(None, max_length=255, description="Full name or first name")
    role: UserRole = UserRole.TEACHER
    
    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        """Convert role to lowercase for case-insensitive input"""
        if isinstance(v, str):
            return v.lower()
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


# Material Schemas
class MaterialCreate(BaseModel):
    title: str


class MaterialResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    title: str
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    glossary: Optional[Dict[str, str]] = None
    file_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# AI Schemas
class GenerateSummaryRequest(BaseModel):
    material_id: UUID4


class GenerateSummaryResponse(BaseModel):
    material_id: UUID4
    summary: str
    glossary: Optional[Dict[str, str]] = None


class QuizQuestion(BaseModel):
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: str


class GenerateQuizRequest(BaseModel):
    material_id: UUID4
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium")


class GenerateQuizResponse(BaseModel):
    quiz_id: UUID4
    material_id: UUID4
    questions: List[QuizQuestion]


# OCR Schemas
class OCRRecognizeResponse(BaseModel):
    text: str
    errors: Optional[List[str]] = None


class OCRQueueItem(BaseModel):
    id: UUID4
    filename: str
    status: str
    created_at: datetime
    

class OCRQueueResponse(BaseModel):
    queue: List[OCRQueueItem]
    total: int


# Analytics Schemas
class DashboardStats(BaseModel):
    total_materials: int
    total_quizzes: int
    total_student_results: int
    average_score: float


class KnowledgeMapData(BaseModel):
    topic: str
    average_score: float
    student_count: int


class AnalyticsDashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activities: List[Dict[str, Any]]


class AnalyticsKnowledgeMapResponse(BaseModel):
    knowledge_map: List[KnowledgeMapData]

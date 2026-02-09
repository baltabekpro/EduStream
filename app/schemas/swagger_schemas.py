"""
Pydantic schemas aligned with swagger.yml specification.
All schemas strictly follow the Swagger contract.
"""
from pydantic import BaseModel, EmailStr, Field, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ===== Enums =====

class UserRole(str, Enum):
    TEACHER = "teacher"
    ADMIN = "admin"


class QuestionType(str, Enum):
    MCQ = "mcq"
    OPEN = "open"
    BOOLEAN = "boolean"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SmartAction(str, Enum):
    EXPLAIN = "explain"
    SIMPLIFY = "simplify"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"


class MaterialStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class OCRConfidence(str, Enum):
    HIGH = "High"
    LOW = "Low"


class ResourceType(str, Enum):
    QUIZ = "quiz"
    OCR_RESULT = "ocr_result"
    MATERIAL = "material"


class StudentTrend(str, Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


# ===== Common Schemas =====

class ErrorResponse(BaseModel):
    """Standard error response format."""
    code: int = Field(..., example=422)
    message: str = Field(..., example="Validation Error")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details by field")


# ===== User & Auth Schemas =====

class UserSettings(BaseModel):
    """User notification settings."""
    notifications: Optional[Dict[str, bool]] = Field(default_factory=lambda: {
        "reports": True,
        "errors": True,
        "lowPerformance": True
    })


class User(BaseModel):
    """User schema matching Swagger."""
    id: UUID4
    email: EmailStr
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    avatar: Optional[str] = None
    role: UserRole
    settings: Optional[UserSettings] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with token and user."""
    token: str
    user: User


# ===== Course Schemas =====

class CourseBase(BaseModel):
    """Base course schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field("#3b82f6", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field("school", max_length=50)


class CourseCreate(CourseBase):
    """Schema for creating a new course."""
    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class CourseResponse(CourseBase):
    """Complete course response with metadata."""
    id: UUID4
    materialsCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


# ===== AI Engine Schemas =====

class QuizConfig(BaseModel):
    """Quiz generation configuration."""
    materialId: UUID4 = Field(..., description="ID документа-источника знаний")
    difficulty: Difficulty = Field(..., description="Влияет на лексику и глубину вопросов")
    count: int = Field(..., ge=1, le=50)
    type: QuestionType
    
    @field_validator('materialId', mode='before')
    @classmethod
    def validate_material_id(cls, v):
        """Validate materialId is a valid UUID."""
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except ValueError:
                raise ValueError(f"materialId must be a valid UUID, got: {v}")
        return v


class Question(BaseModel):
    """Quiz question schema."""
    id: UUID4
    type: QuestionType
    text: str = Field(..., example="Какова основная функция митохондрий?")
    options: Optional[List[str]] = Field(None, description="Варианты ответов (только для MCQ)")
    correctAnswer: str
    explanation: Optional[str] = Field(
        None,
        description="Методическое пояснение от ИИ, почему ответ верен"
    )


class Quiz(BaseModel):
    """Complete quiz schema."""
    id: UUID4
    materialId: UUID4
    questions: List[Question]
    createdAt: datetime
    
    class Config:
        from_attributes = True


class QuizTemplate(BaseModel):
    """Quiz template for gallery."""
    id: int
    title: str = Field(..., example="Входное тестирование")
    desc: str = Field(..., example="15 вопросов для оценки базовых знаний")
    icon: str = Field(..., example="login")
    color: str = Field(..., example="blue")
    config: QuizConfig


class ChatRequest(BaseModel):
    """AI chat request."""
    materialId: Optional[str] = None
    message: str


class SmartActionRequest(BaseModel):
    """Smart selection action request."""
    text: str = Field(..., description="Выделенный фрагмент текста")
    action: SmartAction
    context: Optional[str] = Field(None, description="Опционально: окружающий параграф")


class SmartActionResponse(BaseModel):
    """Smart selection action response."""
    result: str


class RegenerateBlockRequest(BaseModel):
    """Request to regenerate a single block."""
    blockId: str
    currentText: str
    instruction: Optional[str] = Field(None, example="Сделай вопрос сложнее")


class AISessionInfo(BaseModel):
    """AI session information."""
    id: int
    title: str
    date: str
    docId: Optional[str] = None


# ===== OCR Schemas =====

class OCRRegion(BaseModel):
    """OCR region with recognition results."""
    id: str
    label: str = Field(..., example="Вопрос 1")
    original: Optional[str] = Field(None, description="Исходный текст вопроса из базы заданий")
    ocrText: str = Field(..., description="Текст, распознанный с рукописного ввода")
    confidence: OCRConfidence = Field(..., description="Флаг для UI: если Low, слово подчеркивается желтым")
    match: Optional[int] = Field(None, description="Процент семантической близости")


class StudentInfo(BaseModel):
    """Student information in OCR result."""
    name: str
    accuracy: int = Field(..., description="Средний балл точности по всем вопросам")


class StudentResult(BaseModel):
    """Student OCR result."""
    id: UUID4
    student: StudentInfo
    image: str = Field(..., description="URL скана работы")
    questions: List[OCRRegion]


class OCRManualCorrection(BaseModel):
    """Manual correction request."""
    manualScore: Optional[int] = None
    correctedText: Optional[Dict[str, str]] = Field(None, description="Map<RegionID, NewText>")


class BatchApproveRequest(BaseModel):
    """Batch approval request."""
    ids: List[str]


# ===== Dashboard Schemas =====

class PieChartItem(BaseModel):
    """Pie chart data item."""
    name: str
    value: int
    color: str


class NeedsReviewItem(BaseModel):
    """Item needing review."""
    id: str
    name: str
    subject: str
    img: str
    type: str = Field(..., pattern="^(ocr|quiz)$")


class RecentActivityItem(BaseModel):
    """Recent activity item."""
    id: int
    title: str
    source: str
    time: str
    status: str
    statusColor: str
    type: str
    action: str


class DashboardData(BaseModel):
    """Dashboard overview data."""
    pieChart: List[PieChartItem]
    needsReview: List[NeedsReviewItem]
    recentActivity: List[RecentActivityItem]


# ===== Analytics Schemas =====

class PerformanceItem(BaseModel):
    """Performance data item."""
    name: str
    value: int


class TopicItem(BaseModel):
    """Topic score item."""
    name: str
    score: int
    colorKey: str


class StudentMetric(BaseModel):
    """Student metrics for analytics."""
    id: int
    name: str
    status: str
    progress: float
    trend: StudentTrend
    color: str
    avatar: str


class AnalyticsData(BaseModel):
    """Complete analytics data."""
    performance: List[PerformanceItem]
    topics: List[TopicItem]
    students: List[StudentMetric]


# ===== Material Schemas =====

class Material(BaseModel):
    """Material schema matching Swagger."""
    id: str
    title: str
    content: Optional[str] = None
    uploadDate: str
    status: MaterialStatus
    
    class Config:
        from_attributes = True


class MaterialUploadResponse(BaseModel):
    """Material upload response."""
    id: UUID4
    status: MaterialStatus
    message: str = Field(default="Processing started")


class MaterialUpdate(BaseModel):
    """Schema for updating a material."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    course_id: Optional[UUID4] = None


# ===== Share Schemas =====

class ShareConfig(BaseModel):
    """Share configuration."""
    resourceId: str
    resourceType: ResourceType
    viewOnly: Optional[bool] = True
    allowCopy: Optional[bool] = False
    password: Optional[str] = None


class ShareLink(BaseModel):
    """Share link response."""
    url: str


# ===== User Profile Schemas =====

class UserUpdateRequest(BaseModel):
    """User profile update request."""
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    settings: Optional[UserSettings] = None

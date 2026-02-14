import uuid
from sqlalchemy import Column, String, DateTime, Enum, Text, Integer, JSON, ForeignKey, ARRAY, TypeDecorator, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type, otherwise uses String(36).
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value)


class StringArray(TypeDecorator):
    """Platform-independent String Array type.
    Uses PostgreSQL's ARRAY type, otherwise uses JSON.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value


class UserRole(str, enum.Enum):
    """User role enumeration."""
    TEACHER = "teacher"
    ADMIN = "admin"
    STUDENT = "student"


class MaterialStatus(str, enum.Enum):
    """Material processing status."""
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class OCRConfidence(str, enum.Enum):
    """OCR confidence level."""
    HIGH = "High"
    LOW = "Low"


class User(Base):
    """User model for teachers and admins."""
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.TEACHER, nullable=False)
    settings = Column(JSON, nullable=True, default=dict)  # notifications, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    courses = relationship("Course", back_populates="owner", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="owner", cascade="all, delete-orphan")
    student_results = relationship("StudentResult", back_populates="teacher", cascade="all, delete-orphan")
    ai_sessions = relationship("AISession", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    """Course entity for organizing materials."""
    __tablename__ = "courses"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="courses")
    materials = relationship("Material", back_populates="course")


class Material(Base):
    """Educational materials model."""
    __tablename__ = "materials"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Renamed from raw_text for Swagger alignment
    raw_text = Column(Text, nullable=True)  # Keep for backwards compatibility
    summary = Column(Text, nullable=True)
    glossary = Column(JSON, nullable=True)  # {term: definition}
    file_url = Column(String, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(MaterialStatus), default=MaterialStatus.PROCESSING, nullable=False)
    course_id = Column(String, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="materials")
    course = relationship("Course", back_populates="materials")
    quizzes = relationship("Quiz", back_populates="material", cascade="all, delete-orphan")


class Quiz(Base):
    """Quiz and assignments model."""
    __tablename__ = "quizzes"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(), ForeignKey("materials.id"), nullable=False)
    title = Column(String, nullable=True)
    questions = Column(JSON, nullable=False)  # [{question, type, options, correct_answer}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    material = relationship("Material", back_populates="quizzes")
    student_results = relationship("StudentResult", back_populates="quiz", cascade="all, delete-orphan")


class StudentResult(Base):
    """Student results and analytics model."""
    __tablename__ = "student_results"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)  # Teacher ID
    student_identifier = Column(String, nullable=False)  # Student name or ID
    quiz_id = Column(UUID(), ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, nullable=False)  # Percentage
    weak_topics = Column(StringArray, nullable=True)  # List of topics with errors
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="student_results")
    quiz = relationship("Quiz", back_populates="student_results")


class ChatLog(Base):
    """Chat logs for analysis model."""
    __tablename__ = "chat_logs"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(), nullable=False, index=True)
    raw_log = Column(Text, nullable=False)
    analyzed_report = Column(JSON, nullable=True)  # FAQ and activity level
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AISession(Base):
    """AI chat session model for context preservation."""
    __tablename__ = "ai_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="New Chat")
    doc_id = Column(UUID(), ForeignKey("materials.id"), nullable=True)  # Material context
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    messages = Column(JSON, nullable=True, default=list)  # Chat history
    context = Column(JSON, nullable=True, default=dict)  # Session context for regeneration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="ai_sessions")


class OCRResult(Base):
    """OCR processing results model."""
    __tablename__ = "ocr_results"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    student_name = Column(String, nullable=False)
    student_accuracy = Column(Integer, nullable=True)  # Average accuracy across questions
    image_url = Column(String, nullable=False)
    questions = Column(JSON, nullable=False)  # Array of OCRRegion objects
    status = Column(String, default="pending", nullable=False)  # pending, graded, reviewed
    manual_score = Column(Integer, nullable=True)
    course_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PublicLink(Base):
    """Public sharing links model."""
    __tablename__ = "public_links"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    resource_id = Column(String, nullable=False)  # ID of shared resource
    resource_type = Column(String, nullable=False)  # quiz, ocr_result, material
    short_code = Column(String, unique=True, nullable=False, index=True)  # Short URL code
    view_only = Column(Boolean, default=True, nullable=False)
    allow_copy = Column(Boolean, default=False, nullable=False)
    password = Column(String, nullable=True)  # Hashed password if protected
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

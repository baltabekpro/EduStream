import uuid
from sqlalchemy import Column, String, DateTime, Enum, Text, Integer, JSON, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    """User model for teachers and admins."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TEACHER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    materials = relationship("Material", back_populates="owner", cascade="all, delete-orphan")
    student_results = relationship("StudentResult", back_populates="teacher", cascade="all, delete-orphan")


class Material(Base):
    """Educational materials model."""
    __tablename__ = "materials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    glossary = Column(JSON, nullable=True)  # {term: definition}
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="materials")
    quizzes = relationship("Quiz", back_populates="material", cascade="all, delete-orphan")


class Quiz(Base):
    """Quiz and assignments model."""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    questions = Column(JSON, nullable=False)  # [{question, type, options, correct_answer}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    material = relationship("Material", back_populates="quizzes")
    student_results = relationship("StudentResult", back_populates="quiz", cascade="all, delete-orphan")


class StudentResult(Base):
    """Student results and analytics model."""
    __tablename__ = "student_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Teacher ID
    student_identifier = Column(String, nullable=False)  # Student name or ID
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, nullable=False)  # Percentage
    weak_topics = Column(ARRAY(String), nullable=True)  # List of topics with errors
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="student_results")
    quiz = relationship("Quiz", back_populates="student_results")


class ChatLog(Base):
    """Chat logs for analysis model."""
    __tablename__ = "chat_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    raw_log = Column(Text, nullable=False)
    analyzed_report = Column(JSON, nullable=True)  # FAQ and activity level
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

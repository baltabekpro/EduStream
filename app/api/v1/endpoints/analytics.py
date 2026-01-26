from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.dependencies import get_current_teacher
from app.models.models import User, Material, Quiz, StudentResult
from app.schemas.schemas import (
    AnalyticsDashboardResponse,
    AnalyticsKnowledgeMapResponse,
    DashboardStats,
    KnowledgeMapData
)
from typing import List

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Get dashboard statistics for the teacher.
    """
    # Count materials
    total_materials = db.query(func.count(Material.id)).filter(
        Material.user_id == current_user.id
    ).scalar()
    
    # Count quizzes
    total_quizzes = db.query(func.count(Quiz.id)).join(Material).filter(
        Material.user_id == current_user.id
    ).scalar()
    
    # Count student results
    total_student_results = db.query(func.count(StudentResult.id)).filter(
        StudentResult.user_id == current_user.id
    ).scalar()
    
    # Calculate average score
    avg_score = db.query(func.avg(StudentResult.score)).filter(
        StudentResult.user_id == current_user.id
    ).scalar()
    
    if avg_score is None:
        avg_score = 0.0
    
    # Get recent activities (last 10 student results)
    recent_results = db.query(StudentResult).filter(
        StudentResult.user_id == current_user.id
    ).order_by(StudentResult.submission_date.desc()).limit(10).all()
    
    recent_activities = [
        {
            "student": result.student_identifier,
            "quiz_id": str(result.quiz_id),
            "score": result.score,
            "date": result.submission_date.isoformat()
        }
        for result in recent_results
    ]
    
    stats = DashboardStats(
        total_materials=total_materials,
        total_quizzes=total_quizzes,
        total_student_results=total_student_results,
        average_score=float(avg_score)
    )
    
    return {
        "stats": stats,
        "recent_activities": recent_activities
    }


@router.get("/knowledge-map", response_model=AnalyticsKnowledgeMapResponse)
async def get_knowledge_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Get knowledge map data for heat map visualization.
    Shows average scores by topic.
    """
    # Query all student results with weak topics
    results = db.query(StudentResult).filter(
        StudentResult.user_id == current_user.id,
        StudentResult.weak_topics.isnot(None)
    ).all()
    
    # Aggregate data by topic
    topic_data = {}
    
    for result in results:
        if result.weak_topics:
            for topic in result.weak_topics:
                if topic not in topic_data:
                    topic_data[topic] = {
                        "scores": [],
                        "count": 0
                    }
                topic_data[topic]["scores"].append(result.score)
                topic_data[topic]["count"] += 1
    
    # Calculate averages
    knowledge_map = []
    for topic, data in topic_data.items():
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        knowledge_map.append(
            KnowledgeMapData(
                topic=topic,
                average_score=avg_score,
                student_count=data["count"]
            )
        )
    
    return {
        "knowledge_map": knowledge_map
    }

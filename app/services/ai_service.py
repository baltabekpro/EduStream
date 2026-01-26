from typing import Optional, Dict, List
import json
from openai import OpenAI
from app.core.config import settings


class AIService:
    """Service for AI-powered content generation using OpenAI."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def generate_summary(self, text: str) -> Dict[str, any]:
        """
        Generate summary and glossary from educational text.
        Returns dict with 'summary' and 'glossary'.
        """
        if not self.client:
            # Mock response for testing without API key
            return {
                "is_educational": True,
                "summary": "This is a mock summary of the educational material.",
                "glossary": {"Term1": "Definition 1", "Term2": "Definition 2"}
            }
        
        prompt = """Ты опытный методист. Проанализируй следующий текст и создай:
1. Краткий конспект (summary) основных идей
2. Глоссарий (glossary) ключевых терминов и их определений

Если текст не содержит учебного материала, установи is_educational: false.

Верни ответ строго в формате JSON:
{
    "is_educational": true/false,
    "summary": "текст конспекта",
    "glossary": {"термин1": "определение1", "термин2": "определение2"}
}

Текст для анализа:
""" + text[:4000]  # Limit text length
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты опытный методист, создающий учебные материалы."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            raise ValueError(f"Failed to generate summary: {str(e)}")
    
    async def generate_quiz(
        self, 
        text: str, 
        num_questions: int = 5, 
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate quiz questions from educational text.
        Returns list of questions.
        """
        if not self.client:
            # Mock response for testing without API key
            return [
                {
                    "question": "What is the main topic?",
                    "type": "MCQ",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A"
                },
                {
                    "question": "Explain the concept.",
                    "type": "Open",
                    "options": None,
                    "correct_answer": "Sample answer"
                }
            ]
        
        prompt = f"""Ты опытный методист. Создай тест из {num_questions} вопросов по следующему материалу.
Уровень сложности: {difficulty}

Требования:
- Используй типы вопросов: MCQ (множественный выбор) и Open (открытый вопрос)
- Для MCQ предоставь 4 варианта ответа
- Укажи правильный ответ для каждого вопроса

Верни ответ строго в формате JSON массива:
[
    {{
        "question": "текст вопроса",
        "type": "MCQ",
        "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
        "correct_answer": "правильный вариант"
    }},
    {{
        "question": "текст открытого вопроса",
        "type": "Open",
        "options": null,
        "correct_answer": "пример правильного ответа"
    }}
]

Материал для теста:
""" + text[:4000]
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты опытный методист, создающий тесты."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            raise ValueError(f"Failed to generate quiz: {str(e)}")


# Global instance
ai_service = AIService()

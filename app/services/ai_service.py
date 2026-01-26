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
    
    async def generate_quiz_advanced(
        self,
        text: str,
        count: int,
        difficulty: str,
        question_type: str
    ) -> List[Dict]:
        """
        Advanced quiz generation with strict difficulty and type control.
        Implements parametric generation as per Swagger requirements.
        """
        if not self.client:
            # Mock response
            return [
                {
                    "text": f"Sample question {i+1}?",
                    "type": question_type,
                    "options": ["A", "B", "C", "D"] if question_type == "mcq" else None,
                    "correctAnswer": "A",
                    "explanation": "This is the explanation."
                }
                for i in range(count)
            ]
        
        # Difficulty-aware prompt engineering
        difficulty_prompts = {
            "easy": "Вопросы должны проверять базовое понимание и запоминание. Используй простые формулировки.",
            "medium": "Вопросы должны требовать понимания и применения концепций. Используй среднюю лексику.",
            "hard": "Вопросы должны требовать анализа, синтеза и оценки. Используй сложную лексику и многоуровневое мышление."
        }
        
        type_instruction = {
            "mcq": "Создай вопросы с 4 вариантами ответа.",
            "open": "Создай открытые вопросы, требующие развернутого ответа.",
            "boolean": "Создай вопросы типа Верно/Неверно."
        }
        
        prompt = f"""Ты опытный методист. Создай {count} вопросов по материалу.

Уровень сложности: {difficulty}
{difficulty_prompts.get(difficulty, difficulty_prompts["medium"])}

Тип вопросов: {question_type}
{type_instruction.get(question_type, "")}

Для каждого вопроса ОБЯЗАТЕЛЬНО добавь методическое пояснение (explanation), 
почему данный ответ является верным. Это критично для режима 'Презентация' и печати ключей.

Верни ответ строго в формате JSON массива:
[
    {{
        "text": "текст вопроса",
        "type": "{question_type}",
        "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
        "correctAnswer": "правильный ответ",
        "explanation": "методическое пояснение, почему этот ответ верен"
    }}
]

Материал:
""" + text[:4000]
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты опытный методист с глубоким пониманием педагогики."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000,
                timeout=30  # 30 second timeout
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except TimeoutError:
            raise TimeoutError("Quiz generation timeout")
        except Exception as e:
            raise ValueError(f"Failed to generate quiz: {str(e)}")
    
    async def chat_with_context(self, message: str, context: str = "") -> str:
        """
        RAG chat with material context.
        """
        if not self.client:
            return f"Mock AI response to: {message}"
        
        system_prompt = "Ты виртуальный ассистент учителя. Помогай создавать учебные материалы."
        if context:
            system_prompt += f"\n\nКонтекст из материала:\n{context}"
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Chat failed: {str(e)}")
    
    async def perform_smart_action(
        self,
        text: str,
        action: str,
        context: Optional[str] = None
    ) -> str:
        """
        Perform smart text transformations.
        Actions: explain, simplify, translate, summarize
        """
        if not self.client:
            return f"Mock {action} of: {text[:50]}..."
        
        action_prompts = {
            "explain": "Объясни следующий текст простыми словами для школьника:",
            "simplify": "Упрости следующий текст, сохранив главный смысл:",
            "translate": "Переведи следующий текст на английский язык:",
            "summarize": "Создай краткое резюме следующего текста:"
        }
        
        prompt = action_prompts.get(action, action_prompts["explain"])
        if context:
            prompt += f"\n\nКонтекст: {context}\n\n"
        prompt += f"Текст: {text}"
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты опытный педагог."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Smart action failed: {str(e)}")
    
    async def regenerate_question(
        self,
        current_text: str,
        instruction: str
    ) -> Dict:
        """
        Regenerate a single question with context preservation.
        """
        if not self.client:
            return {
                "text": "Regenerated question?",
                "type": "mcq",
                "options": ["A", "B", "C", "D"],
                "correctAnswer": "A",
                "explanation": "Explanation"
            }
        
        prompt = f"""Ты методист. У тебя есть вопрос теста, который нужно улучшить.

Текущий вопрос:
{current_text}

Инструкция по улучшению:
{instruction}

Создай улучшенную версию вопроса, следуя инструкции.

Верни ответ в формате JSON:
{{
    "text": "текст вопроса",
    "type": "mcq",
    "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
    "correctAnswer": "правильный ответ",
    "explanation": "методическое пояснение"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты опытный методист."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            raise ValueError(f"Regeneration failed: {str(e)}")


# Global instance
ai_service = AIService()

"""
Комплексный тест платформы EduStream для учителей.
Этот скрипт проверяет все основные функции платформы в реалистичном сценарии.
"""

import requests
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional
from io import BytesIO


class EduStreamTester:
    """Класс для комплексного тестирования платформы EduStream."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.teacher_id: Optional[str] = None
        self.material_id: Optional[str] = None
        self.quiz_id: Optional[str] = None
        
        # Статистика тестов
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование с цветным выводом."""
        colors = {
            "INFO": "\033[94m",  # Синий
            "SUCCESS": "\033[92m",  # Зеленый
            "WARNING": "\033[93m",  # Желтый
            "ERROR": "\033[91m",  # Красный
            "RESET": "\033[0m"
        }
        print(f"{colors.get(level, '')}{level}: {message}{colors['RESET']}")
    
    def test_case(self, name: str, func):
        """Декоратор для тестовых кейсов."""
        def wrapper(*args, **kwargs):
            self.log(f"\n{'='*60}")
            self.log(f"Тест: {name}", "INFO")
            self.log(f"{'='*60}")
            try:
                result = func(*args, **kwargs)
                self.tests_passed += 1
                self.test_results.append({"name": name, "status": "PASSED", "error": None})
                self.log(f"✅ Тест пройден: {name}", "SUCCESS")
                return result
            except Exception as e:
                self.tests_failed += 1
                self.test_results.append({"name": name, "status": "FAILED", "error": str(e)})
                self.log(f"❌ Тест провален: {name}", "ERROR")
                self.log(f"Ошибка: {str(e)}", "ERROR")
                # Не останавливаем выполнение, продолжаем тестирование
                return None
        return wrapper
    
    def print_summary(self):
        """Вывод итоговой статистики."""
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        self.log("\n" + "="*60, "INFO")
        self.log("ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ", "INFO")
        self.log("="*60, "INFO")
        self.log(f"Всего тестов: {total}", "INFO")
        self.log(f"Успешно: {self.tests_passed}", "SUCCESS")
        self.log(f"Провалено: {self.tests_failed}", "ERROR")
        self.log(f"Успешность: {success_rate:.1f}%", "INFO")
        
        if self.tests_failed > 0:
            self.log("\nПроваленные тесты:", "WARNING")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    self.log(f"  - {result['name']}: {result['error']}", "ERROR")
    
    def run_all_tests(self):
        """Запуск всех тестов в правильной последовательности."""
        self.log("Начало комплексного тестирования платформы EduStream", "INFO")
        
        # 1. Тест регистрации
        self.test_case("1. Регистрация нового учителя", self.test_register)()
        
        # 2. Тест входа
        self.test_case("2. Вход в систему", self.test_login)()
        
        # 3. Тест загрузки материала
        self.test_case("3. Загрузка учебного материала", self.test_upload_material)()
        
        # 4. Тест генерации конспекта
        self.test_case("4. Генерация конспекта и глоссария", self.test_generate_summary)()
        
        # 5. Тест генерации теста
        self.test_case("5. Генерация теста по материалу", self.test_generate_quiz)()
        
        # 6. Тест OCR
        self.test_case("6. OCR - Распознавание текста", self.test_ocr_recognize)()
        
        # 7. Тест аналитики
        self.test_case("7. Просмотр аналитики", self.test_analytics_dashboard)()
        
        # 8. Тест карты знаний
        self.test_case("8. Карта знаний", self.test_knowledge_map)()
        
        # 9. Тест списка курсов
        self.test_case("9. Список курсов", self.test_list_courses)()
        
        # 10. Тест списка материалов
        self.test_case("10. Список всех материалов", self.test_list_materials)()
        
        # 11. Тест получения конкретного материала
        self.test_case("11. Получение материала по ID", self.test_get_material)()
        
        # Итоговая статистика
        self.print_summary()
    
    def test_register(self):
        """Тест 1: Регистрация нового учителя."""
        url = f"{self.base_url}/api/v1/auth/register"
        
        # Уникальный email для каждого запуска
        timestamp = int(time.time())
        email = f"teacher_test_{timestamp}@example.com"
        
        payload = {
            "email": email,
            "password": "SecurePass123!",
            "first_name": "Тестовый",
            "last_name": "Учитель",
            "role": "teacher"
        }
        
        self.log(f"Отправка POST запроса: {url}")
        self.log(f"Данные: {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # Проверки
            assert "access_token" in data, "access_token отсутствует в ответе"
            assert "user" in data, "user отсутствует в ответе"
            assert data["user"]["email"] == email, "Email не совпадает"
            
            # Сохраняем токен для дальнейших тестов
            self.access_token = data["access_token"]
            self.teacher_id = data["user"]["id"]
            
            self.log("Токен получен и сохранен", "SUCCESS")
        else:
            self.log(f"Ошибка: {response.text}", "ERROR")
            raise Exception(f"Регистрация провалена: {response.status_code}")
    
    def test_login(self):
        """Тест 2: Вход в систему."""
        if not self.access_token:
            self.log("Используем существующего пользователя", "WARNING")
            
            url = f"{self.base_url}/api/v1/auth/login"
            payload = {
                "email": "teacher@example.com",
                "password": "password123"
            }
            
            self.log(f"Отправка POST запроса: {url}")
            response = requests.post(url, json=payload)
            
            self.log(f"Статус код: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                assert "access_token" in data, "access_token отсутствует"
                self.access_token = data["access_token"]
                self.log("Вход выполнен успешно", "SUCCESS")
            else:
                raise Exception(f"Вход провален: {response.text}")
        else:
            self.log("Токен уже получен при регистрации", "INFO")
    
    def test_upload_material(self):
        """Тест 3: Загрузка учебного материала."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/materials/upload"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Создаем тестовый текстовый файл с учебным материалом
        test_content = """
        Введение в квантовую механику
        
        Квантовая механика - это раздел физики, изучающий поведение материи и энергии
        на атомном и субатомном уровнях. Основные принципы включают:
        
        1. Принцип неопределенности Гейзенберга
        2. Волновая функция
        3. Квантование энергии
        4. Суперпозиция состояний
        
        Глоссарий:
        - Квант - минимальная порция энергии
        - Фотон - квант электромагнитного излучения
        - Волновая функция - математическое описание квантового состояния
        """
        
        # Создаем временный файл
        files = {
            'file': ('quantum_mechanics.txt', BytesIO(test_content.encode('utf-8')), 'text/plain')
        }
        
        self.log(f"Отправка POST запроса: {url}")
        self.log(f"Загрузка файла: quantum_mechanics.txt")
        
        response = requests.post(url, headers=headers, files=files)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert "id" in data, "ID материала отсутствует"
            assert "title" in data, "Название материала отсутствует"
            
            self.material_id = data["id"]
            self.log(f"Материал загружен с ID: {self.material_id}", "SUCCESS")
        else:
            raise Exception(f"Загрузка материала провалена: {response.text}")
    
    def test_generate_summary(self):
        """Тест 4: Генерация конспекта и глоссария."""
        if not self.access_token or not self.material_id:
            raise Exception("Требуется материал")
        
        url = f"{self.base_url}/api/v1/ai/generate-summary"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {"material_id": self.material_id}
        
        self.log(f"Отправка POST запроса: {url}")
        self.log(f"Данные: {json.dumps(payload)}")
        self.log("⏳ Ожидание ответа от ИИ (может занять 10-30 секунд)...", "WARNING")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert "summary" in data, "Конспект отсутствует"
            assert "glossary" in data, "Глоссарий отсутствует"
            
            self.log("Конспект успешно сгенерирован", "SUCCESS")
            self.log(f"Длина конспекта: {len(data['summary'])} символов")
            self.log(f"Количество терминов в глоссарии: {len(data['glossary'])}")
        else:
            raise Exception(f"Генерация конспекта провалена: {response.text}")
    
    def test_generate_quiz(self):
        """Тест 5: Генерация теста по материалу."""
        if not self.access_token or not self.material_id:
            raise Exception("Требуется материал")
        
        url = f"{self.base_url}/api/v1/ai/generate-quiz"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "material_id": self.material_id,
            "num_questions": 3,
            "difficulty": "medium"
        }
        
        self.log(f"Отправка POST запроса: {url}")
        self.log(f"Данные: {json.dumps(payload)}")
        self.log("⏳ Ожидание ответа от ИИ (может занять 10-30 секунд)...", "WARNING")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert "quiz_id" in data, "ID теста отсутствует"
            assert "questions" in data, "Вопросы отсутствуют"
            assert len(data["questions"]) == 3, "Количество вопросов не совпадает"
            
            self.quiz_id = data["quiz_id"]
            self.log(f"Тест успешно сгенерирован с ID: {self.quiz_id}", "SUCCESS")
            self.log(f"Количество вопросов: {len(data['questions'])}")
        else:
            raise Exception(f"Генерация теста провалена: {response.text}")
    
    def test_ocr_recognize(self):
        """Тест 6: OCR - Распознавание текста из изображения."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/ocr/recognize"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Создаем простое тестовое изображение с текстом
        # Для реального теста нужно настоящее изображение
        # Здесь используем заглушку
        
        self.log("Создание тестового изображения с текстом...", "INFO")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Создаем простое изображение с текстом
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Пытаемся использовать системный шрифт
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                # Если не удалось, используем стандартный
                font = ImageFont.load_default()
            
            text = "Hello World\nTest 123"
            draw.text((50, 50), text, fill='black', font=font)
            
            # Сохраняем в байты
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            files = {
                'file': ('test_image.png', img_bytes, 'image/png')
            }
            
            self.log(f"Отправка POST запроса: {url}")
            self.log("⏳ Распознавание текста...", "WARNING")
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
            self.log(f"Статус код: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                assert "text" in data, "Распознанный текст отсутствует"
                
                self.log("Текст успешно распознан", "SUCCESS")
                self.log(f"Распознанный текст: {data['text']}")
            else:
                raise Exception(f"OCR провален: {response.text}")
        
        except ImportError:
            self.log("Pillow не установлен, пропускаем OCR тест", "WARNING")
            self.log("Установите Pillow: pip install Pillow", "INFO")
    
    def test_analytics_dashboard(self):
        """Тест 7: Просмотр аналитики."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/analytics/dashboard"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        self.log(f"Отправка GET запроса: {url}")
        
        response = requests.get(url, headers=headers)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert "stats" in data, "Статистика отсутствует"
            assert "recent_activities" in data, "Недавние активности отсутствуют"
            
            stats = data["stats"]
            self.log("Статистика получена:", "SUCCESS")
            self.log(f"  - Всего материалов: {stats['total_materials']}")
            self.log(f"  - Всего тестов: {stats['total_quizzes']}")
            self.log(f"  - Результатов студентов: {stats['total_student_results']}")
            self.log(f"  - Средний балл: {stats['average_score']:.2f}")
        else:
            raise Exception(f"Получение аналитики провалено: {response.text}")
    
    def test_knowledge_map(self):
        """Тест 8: Карта знаний."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/analytics/knowledge-map"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        self.log(f"Отправка GET запроса: {url}")
        
        response = requests.get(url, headers=headers)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert "topics" in data, "Темы отсутствуют"
            
            self.log("Карта знаний получена", "SUCCESS")
            self.log(f"Количество тем: {len(data['topics'])}")
        else:
            raise Exception(f"Получение карты знаний провалено: {response.text}")
    
    def test_list_courses(self):
        """Тест 9: Список курсов."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/courses/"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        self.log(f"Отправка GET запроса: {url}")
        
        response = requests.get(url, headers=headers)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Ответ: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            assert isinstance(data, list), "Ответ должен быть списком"
            
            self.log("Список курсов получен", "SUCCESS")
            self.log(f"Количество курсов: {len(data)}")
        else:
            raise Exception(f"Получение списка курсов провалено: {response.text}")
    
    def test_list_materials(self):
        """Тест 10: Список всех материалов."""
        if not self.access_token:
            raise Exception("Требуется аутентификация")
        
        url = f"{self.base_url}/api/v1/materials/"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        self.log(f"Отправка GET запроса: {url}")
        
        response = requests.get(url, headers=headers)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Количество материалов: {len(data)}")
            
            assert isinstance(data, list), "Ответ должен быть списком"
            
            if len(data) > 0:
                self.log(f"Первый материал: {data[0]['title']}", "INFO")
            
            self.log("Список материалов получен", "SUCCESS")
        else:
            raise Exception(f"Получение списка материалов провалено: {response.text}")
    
    def test_get_material(self):
        """Тест 11: Получение конкретного материала по ID."""
        if not self.access_token or not self.material_id:
            raise Exception("Требуется материал")
        
        url = f"{self.base_url}/api/v1/materials/{self.material_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        self.log(f"Отправка GET запроса: {url}")
        
        response = requests.get(url, headers=headers)
        
        self.log(f"Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Материал получен: {data['title']}", "SUCCESS")
            
            assert data["id"] == self.material_id, "ID не совпадает"
            
            self.log(f"  - ID: {data['id']}")
            self.log(f"  - Название: {data['title']}")
            if data.get('summary'):
                self.log(f"  - Есть конспект: Да")
            if data.get('glossary'):
                self.log(f"  - Есть глоссарий: Да")
        else:
            raise Exception(f"Получение материала провалено: {response.text}")


def main():
    """Главная функция для запуска тестов."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПЛАТФОРМЫ EDUSTREAM         ║
    ║                                                              ║
    ║  Этот скрипт тестирует все основные функции платформы       ║
    ║  в типичном сценарии использования учителем                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # URL API (можно изменить при необходимости)
    base_url = os.getenv("EDUSTREAM_API_URL", "http://localhost:8000")
    
    print(f"\n🌐 API URL: {base_url}")
    print(f"⏰ Время запуска: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60 + "\n")
    
    # Проверка доступности API
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ API доступен (статус: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ API недоступен: {e}")
        print("\n⚠️ Убедитесь, что сервер запущен:")
        print("   cd EduStream")
        print("   uvicorn app.main:app --reload")
        return
    
    # Создаем и запускаем тестер
    tester = EduStreamTester(base_url)
    tester.run_all_tests()
    
    print("\n" + "="*60)
    print("Тестирование завершено!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

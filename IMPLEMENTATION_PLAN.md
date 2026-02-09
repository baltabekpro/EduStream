# EduStream - Анализ реализации функционала

## 🎯 Цель платформы (из документации)

**EduStream** - виртуальный помощник учителя для:
1. ✅ Управления образовательными материалами (PDF/DOCX)
2. ✅ AI-генерации контента (тесты, конспекты, чат)
3. ✅ OCR-распознавания рукописных работ учеников
4. ✅ Аналитики успеваемости класса
5. ⚠️ Управления курсами (частично)

## 📊 Текущее состояние реализации

### ✅ Полностью реализовано:

#### Backend API:
- **Auth** (`/auth`):
  - ✅ POST `/auth/register` - Регистрация
  - ✅ POST `/auth/login` - Логин
  - ✅ POST `/auth/refresh` - Обновление токена

- **Users** (`/users`):
  - ✅ GET `/users/me` - Профиль пользователя
  - ✅ PATCH `/users/me` - Обновление профиля

- **Materials** (`/materials`):
  - ✅ GET `/materials/` - Список материалов
  - ✅ POST `/materials/` - Загрузка файла
  - ✅ GET `/materials/{id}` - Получение материала

- **AI** (`/ai`):
  - ✅ GET `/ai/templates` - Шаблоны тестов
  - ✅ POST `/ai/chat` - RAG чат
  - ✅ POST `/ai/smart-action` - Умные действия
  - ✅ POST `/ai/generate-quiz` - Генерация теста
  - ✅ POST `/ai/regenerate-block` - Регенерация вопроса
  - ✅ GET `/ai/sessions` - История чатов

- **OCR** (`/ocr`):
  - ✅ POST `/ocr/recognize` - Распознавание (не используется на фронте)
  - ✅ GET `/ocr/queue` - Очередь на проверку
  - ✅ GET `/ocr/results/{id}` - Результат по ID
  - ✅ PATCH `/ocr/results/{id}` - Ручная коррекция
  - ✅ POST `/ocr/batch-approve` - Пакетное подтверждение

- **Analytics** (`/analytics`):
  - ✅ GET `/analytics/performance` - Аналитика

- **Dashboard** (`/dashboard`):
  - ✅ GET `/dashboard/overview` - Главный экран

- **Courses** (`/courses`):
  - ✅ GET `/courses/` - Список курсов (агрегация из Materials)

#### Frontend:
- ✅ Аутентификация (login, register)
- ✅ Dashboard с виджетами
- ✅ Загрузка материалов через drag-n-drop
- ✅ OCR проверка
- ✅ AI Ассистент
- ✅ Аналитика

### ⚠️ Частично реализовано:

#### Backend:
- **Courses**:
  - ✅ GET `/courses/` - Список курсов
  - ❌ POST `/courses/` - **ОТСУТСТВУЕТ** создание курса
  - ❌ PATCH `/courses/{id}` - **ОТСУТСТВУЕТ** редактирование
  - ❌ DELETE `/courses/{id}` - **ОТСУТСТВУЕТ** удаление
  - ⚠️ Нет модели Course в БД (только course_id в Material)

- **Materials**:
  - ✅ GET, POST
  - ❌ PATCH `/materials/{id}` - **ОТСУТСТВУЕТ** редактирование
  - ❌ DELETE `/materials/{id}` - **ОТСУТСТВУЕТ** удаление

#### Frontend:
- ⚠️ Нет UI для создания курсов
- ⚠️ Нет UI для редактирования материалов
- ⚠️ Нет UI для удаления

### ❌ Не реализовано:

1. **Модель Course в БД** - курсы существуют только как строки в Material.course_id
2. **CRUD для курсов** - только чтение
3. **CRUD для материалов** - только создание и чтение
4. **Экспорт отчетов** (`/reports/export`) - упомянут в swagger.yml, но не реализован
5. **Share links** (`/share/create`) - backend реализован, frontend не использует
6. **Категоризация материалов** - нет тегов, папок, курсов как сущностей

## 🔧 План реализации отсутствующего функционала

### Этап 1: Модель Course в БД (Backend)

**Файл:** `app/models/models.py`

```python
class Course(Base):
    """Course model for organizing materials."""
    __tablename__ = "courses"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", backref="courses")
    materials = relationship("Material", back_populates="course")
```

**Изменения в Material:**
```python
class Material(Base):
    # Заменить course_id: String на:
    course_id = Column(UUID(), ForeignKey("courses.id"), nullable=True)
    
    # Добавить relationship:
    course = relationship("Course", back_populates="materials")
```

**Миграция Alembic:**
```bash
alembic revision --autogenerate -m "add_course_model"
alembic upgrade head
```

### Этап 2: CRUD endpoints для Course (Backend)

**Файл:** `app/api/v1/endpoints/courses.py`

```python
@router.post("/", response_model=CourseResponse, status_code=201)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создание нового курса."""
    
@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление курса."""
    
@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удаление курса."""
```

### Этап 3: CRUD endpoints для Materials (Backend)

**Файл:** `app/api/v1/endpoints/materials_swagger.py`

```python
@router.patch("/{id}", response_model=Material)
async def update_material(
    id: UUID,
    update_data: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление материала."""
    
@router.delete("/{id}", status_code=204)
async def delete_material(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удаление материала."""
```

### Этап 4: Schemas для CRUD (Backend)

**Файл:** `app/schemas/swagger_schemas.py`

```python
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    color: Optional[str] = "#3b82f6"
    icon: Optional[str] = "school"

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class CourseResponse(BaseModel):
    id: UUID4
    title: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    materialsCount: int
    created_at: datetime

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    course_id: Optional[UUID4] = None
```

### Этап 5: Frontend API Services

**Файл:** `EduStream-Frontend/lib/api.ts`

```typescript
export const CourseService = {
  getAll: async (): Promise<Course[]> => { /* EXISTS */ },
  
  create: async (data: CourseCreate): Promise<Course> => {
    return request<Course>('/courses/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  update: async (id: string, data: CourseUpdate): Promise<Course> => {
    return request<Course>(`/courses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  
  delete: async (id: string): Promise<void> => {
    await request(`/courses/${id}`, { method: 'DELETE' });
  },
};

export const MaterialService = {
  update: async (id: string, data: MaterialUpdate): Promise<Material> => {
    return request<Material>(`/materials/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  
  delete: async (id: string): Promise<void> => {
    await request(`/materials/${id}`, { method: 'DELETE' });
  },
};
```

### Этап 6: Frontend UI Components

**Новые компоненты:**

1. **CreateCourseModal.tsx**
   - Форма создания курса
   - Выбор цвета и иконки
   - Валидация

2. **EditCourseModal.tsx**
   - Редактирование названия, описания
   - Изменение цвета/иконки

3. **CoursesList.tsx**
   - Список курсов с карточками
   - Кнопки редактирования/удаления
   - Drag-n-drop для сортировки (опционально)

4. **MaterialItem.tsx**
   - Карточка материала с меню действий
   - Редактирование названия
   - Перенос в другой курс
   - Удаление

**Обновление существующих:**

5. **Dashboard.tsx**
   - Добавить кнопку "Создать курс"
   - Показывать курсы в виджете

6. **Sidebar.tsx**
   - Список курсов для быстрой навигации
   - Индикатор количества материалов

### Этап 7: Context для курсов (Frontend)

**Файл:** `EduStream-Frontend/context/CourseContext.tsx`

Обновить для работы с полными объектами Course вместо строк:

```typescript
interface CourseContextType {
  courses: Course[];
  selectedCourse: Course | null;
  selectCourse: (course: Course | null) => void;
  createCourse: (data: CourseCreate) => Promise<Course>;
  updateCourse: (id: string, data: CourseUpdate) => Promise<Course>;
  deleteCourse: (id: string) => Promise<void>;
  refreshCourses: () => Promise<void>;
}
```

## 📝 Приоритеты реализации

### 🔴 Критичные (P0):
1. **Создание курсов** - без этого нельзя организовать материалы
2. **Модель Course в БД** - миграция данных
3. **POST /courses/** endpoint

### 🟡 Важные (P1):
4. **Редактирование курсов** - PATCH /courses/{id}
5. **Удаление курсов** - DELETE /courses/{id}
6. **UI для управления курсами** - модалы, формы

### 🟢 Желательные (P2):
7. **Редактирование материалов** - PATCH /materials/{id}
8. **Удаление материалов** - DELETE /materials/{id}
9. **Перенос материалов между курсами**
10. **Экспорт отчетов** - /reports/export

### 🔵 Nice-to-have (P3):
11. **Share links UI** - использование /share/create
12. **Категоризация курсов** - теги, архив
13. **Поиск по материалам**
14. **Bulk operations** - массовое удаление/перенос

## 🎯 MVP для полноценной работы

Минимальный набор для запуска:

1. ✅ Модель Course в БД
2. ✅ POST /courses/ - создание
3. ✅ PATCH /courses/{id} - редактирование
4. ✅ UI CreateCourseModal
5. ✅ Обновление Dashboard с кнопкой создания
6. ✅ Миграция существующих course_id в таблицу courses

## 🗓️ Оценка времени

- **Этап 1-2 (Backend Model + CRUD):** ~2 часа
- **Этап 3-4 (Materials CRUD + Schemas):** ~1 час
- **Этап 5-6 (Frontend Services + UI):** ~3 часа
- **Этап 7 (Context integration):** ~1 час
- **Тестирование и отладка:** ~1 час

**Итого:** ~8 часов работы

## 📌 Следующие шаги

1. Создать модель Course и миграцию
2. Реализовать CRUD endpoints
3. Обновить frontend API services
4. Создать UI компоненты
5. Интегрировать в Dashboard
6. Тестирование
7. Деплой

---

**Статус:** 📋 План готов к реализации
**Дата:** 09.02.2026

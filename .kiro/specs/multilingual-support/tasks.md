# Implementation Plan: Multilingual Support

## Overview

Реализация полной поддержки двух языков (русский и казахский) в приложении EduStream. План включает расширение существующего LanguageContext, создание полных переводов, модификацию AI сервиса для генерации контента на выбранном языке, и обеспечение локализации всех UI компонентов.

## Tasks

- [x] 1. Расширить LanguageContext для поддержки казахского языка
  - [x] 1.1 Обновить тип Language для включения 'kk'
    - Добавить 'kk' в тип `Language = 'ru' | 'en' | 'kk'`
    - Обновить интерфейс LanguageContextType
    - _Requirements: 1.1, 8.2_
  
  - [x] 1.2 Создать полный словарь переводов на казахский язык
    - Создать структуру переводов с namespace-ключами (nav.*, dash.*, ocr.*, ai.*, analytics.*, settings.*, auth.*)
    - Перевести все существующие русские строки на казахский
    - Обеспечить культурно-соответствующую терминологию
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1, 5.3, 8.1_
  
  - [ ]* 1.3 Написать property test для полноты словаря переводов
    - **Property 2: Translation Dictionary Completeness**
    - **Validates: Requirements 2.1**
  
  - [x] 1.4 Реализовать сохранение языковых предпочтений в localStorage
    - Сохранять выбранный язык при вызове setLanguage
    - Загружать сохраненный язык при инициализации контекста
    - Установить 'ru' как язык по умолчанию если предпочтение отсутствует
    - _Requirements: 1.3, 1.4, 1.5, 12.2_
  
  - [ ]* 1.5 Написать property test для персистентности языковых предпочтений
    - **Property 1: Language Preference Persistence**
    - **Validates: Requirements 1.3, 1.4, 12.1**
  
  - [x] 1.6 Реализовать fallback механизм для отсутствующих ключей
    - Возвращать сам ключ если перевод не найден
    - Логировать предупреждение в development режиме
    - _Requirements: 8.5_
  
  - [ ]* 1.7 Написать property test для fallback механизма
    - **Property 13: Translation Key Fallback**
    - **Validates: Requirements 8.4, 8.5**

- [x] 2. Создать компонент Language Switcher
  - [x] 2.1 Реализовать UI компонент переключателя языка
    - Создать компонент с отображением трех опций: Русский | English | Қазақша
    - Добавить визуальный индикатор активного языка
    - Реализовать обработчик клика для смены языка
    - Добавить визуальную обратную связь при смене языка
    - Обеспечить keyboard navigation для accessibility
    - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 2.2 Интегрировать Language Switcher в страницу Settings
    - Добавить компонент в EduStream-Frontend/pages/Settings.tsx
    - Разместить в видимой и доступной позиции
    - _Requirements: 6.1_
  
  - [ ]* 2.3 Написать unit тесты для Language Switcher
    - Тест рендеринга всех языковых опций
    - Тест визуального индикатора активного языка
    - Тест вызова setLanguage при клике
    - Тест keyboard navigation

- [x] 3. Реализовать локализацию форматирования дат и чисел
  - [x] 3.1 Создать утилиты для locale-aware форматирования
    - Реализовать функцию formatDate(date, locale)
    - Реализовать функцию formatNumber(number, locale)
    - Реализовать функцию formatRelativeTime(date, locale)
    - Реализовать функцию sortByLocale(array, locale)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 2.8_
  
  - [ ]* 3.2 Написать property тесты для форматирования
    - **Property 14: Date Formatting Locale Consistency**
    - **Property 15: Number Formatting Locale Consistency**
    - **Property 16: Locale-Aware Text Sorting**
    - **Property 17: Relative Time Translation**
    - **Validates: Requirements 10.1, 10.2, 10.4, 10.5**
  
  - [x] 3.3 Применить locale-aware форматирование во всех компонентах
    - Обновить Dashboard для форматирования дат и чисел
    - Обновить Analytics для форматирования метрик
    - Обновить все компоненты с отображением времени
    - _Requirements: 10.1, 10.2, 10.5_

- [x] 4. Checkpoint - Проверить работу frontend локализации
  - Убедиться что все тесты проходят, спросить пользователя если возникли вопросы.

- [x] 5. Добавить поддержку Accept-Language header в API клиенте
  - [x] 5.1 Модифицировать API клиент для включения Accept-Language header
    - Обновить EduStream-Frontend/lib/api.ts
    - Читать текущий locale из LanguageContext
    - Добавлять Accept-Language header во все запросы
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ]* 5.2 Написать property test для включения language header
    - **Property 11: Frontend API Request Language Header**
    - **Validates: Requirements 7.1, 7.2, 7.3**
  
  - [ ]* 5.3 Написать integration тесты для API клиента
    - Мокировать API клиент
    - Проверить наличие Accept-Language header
    - Проверить соответствие значения header текущему locale

- [x] 6. Реализовать обработку Accept-Language header в Backend
  - [x] 6.1 Создать dependency функцию для извлечения языка из header
    - Создать функцию get_language в app/api/dependencies.py
    - Парсить Accept-Language header
    - Валидировать язык против поддерживаемых (ru, kk, en)
    - Возвращать 'ru' по умолчанию для неподдерживаемых/отсутствующих значений
    - _Requirements: 3.1, 3.2, 3.3, 12.5_
  
  - [ ]* 6.2 Написать property test для валидации языкового параметра
    - **Property 3: Backend Language Parameter Validation**
    - **Validates: Requirements 3.2, 3.3, 12.5**
  
  - [ ]* 6.3 Написать unit тесты для get_language
    - Тест парсинга валидных language кодов
    - Тест дефолта для невалидных кодов
    - Тест обработки отсутствующего header
    - Тест обработки некорректного формата header

- [x] 7. Обновить все API endpoints для поддержки языкового параметра
  - [x] 7.1 Добавить language dependency в AI endpoints
    - Обновить /ai/generate-summary
    - Обновить /ai/generate-quiz
    - Обновить /ai/generate-quiz-advanced
    - Обновить /ai/chat
    - Обновить /ai/smart-action
    - Обновить /ai/evaluate-assignment
    - Обновить /ai/generate-assignment
    - Добавить `language: str = Depends(get_language)` в сигнатуры
    - _Requirements: 3.1, 7.4_
  
  - [x] 7.2 Добавить metadata с примененным locale в API ответы
    - Включить поле "language" в response metadata
    - _Requirements: 3.5_
  
  - [ ]* 7.3 Написать property test для locale metadata в ответах
    - **Property 4: API Response Locale Metadata**
    - **Validates: Requirements 3.5**
  
  - [x] 7.3 Реализовать локализованные сообщения об ошибках
    - Создать словарь сообщений об ошибках для ru и kk
    - Возвращать ошибки на запрошенном языке
    - _Requirements: 3.4_
  
  - [ ]* 7.4 Написать property test для propagation языка в backend
    - **Property 12: Backend Language Propagation**
    - **Validates: Requirements 7.4**
  
  - [ ]* 7.5 Написать property test для обратной совместимости
    - **Property 19: Backward Compatibility**
    - **Validates: Requirements 12.4**

- [x] 8. Модифицировать AI Service для генерации контента на выбранном языке
  - [x] 8.1 Обновить сигнатуры методов AI Service
    - Добавить параметр `language: str = 'ru'` во все методы
    - Обновить generate_summary
    - Обновить generate_quiz
    - Обновить generate_quiz_advanced
    - Обновить chat_with_context
    - Обновить perform_smart_action
    - Обновить evaluate_assignment_submission
    - Обновить generate_assignment
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 8.2 Модифицировать промпты для включения языковых инструкций
    - Добавить явные инструкции "Respond in Russian/Kazakh language" в промпты
    - Создать language-specific prompt templates для ru и kk
    - Обеспечить использование образовательной терминологии для казахского
    - _Requirements: 4.6, 9.1, 9.2, 9.3_
  
  - [ ]* 8.3 Написать property test для языковых инструкций в промптах
    - **Property 10: AI Prompt Language Instructions**
    - **Validates: Requirements 4.6, 9.1**
  
  - [x] 8.4 Реализовать генерацию summary на выбранном языке
    - Модифицировать generate_summary для использования language параметра
    - Обновить промпт с языковыми инструкциями
    - _Requirements: 4.1_
  
  - [ ]* 8.5 Написать property test для AI summary language consistency
    - **Property 5: AI Summary Language Consistency**
    - **Validates: Requirements 4.1**
  
  - [x] 8.6 Реализовать генерацию quiz на выбранном языке
    - Модифицировать generate_quiz и generate_quiz_advanced
    - Обновить промпты с языковыми инструкциями
    - Обеспечить что вопросы, опции и объяснения на запрошенном языке
    - _Requirements: 4.2, 9.3_
  
  - [ ]* 8.7 Написать property test для AI quiz language consistency
    - **Property 6: AI Quiz Language Consistency**
    - **Validates: Requirements 4.2**
  
  - [x] 8.8 Реализовать chat на выбранном языке
    - Модифицировать chat_with_context
    - Обновить промпт с языковыми инструкциями
    - _Requirements: 4.3_
  
  - [ ]* 8.9 Написать property test для AI chat language consistency
    - **Property 7: AI Chat Language Consistency**
    - **Validates: Requirements 4.3**
  
  - [x] 8.10 Реализовать smart actions на выбранном языке
    - Модифицировать perform_smart_action
    - Обновить промпты для всех действий (explain, simplify, translate, summarize)
    - _Requirements: 4.4_
  
  - [ ]* 8.11 Написать property test для AI smart action language consistency
    - **Property 8: AI Smart Action Language Consistency**
    - **Validates: Requirements 4.4**
  
  - [x] 8.12 Реализовать evaluation на выбранном языке
    - Модифицировать evaluate_assignment_submission
    - Обновить промпт для генерации feedback, strengths, improvements на запрошенном языке
    - _Requirements: 4.5_
  
  - [ ]* 8.13 Написать property test для AI evaluation language consistency
    - **Property 9: AI Assignment Evaluation Language Consistency**
    - **Validates: Requirements 4.5**
  
  - [x] 8.14 Добавить валидацию соответствия языка сгенерированного контента
    - Опционально: проверять что AI ответ соответствует запрошенному языку
    - Возвращать ошибку при несоответствии
    - _Requirements: 4.7, 9.5_

- [x] 9. Checkpoint - Проверить работу AI локализации
  - Убедиться что все тесты проходят, спросить пользователя если возникли вопросы.

- [x] 10. Обеспечить корректную обработку смешанного контента
  - [x] 10.1 Проверить что пользовательский контент не переводится автоматически
    - Убедиться что названия курсов, материалов, заметок остаются в оригинальном языке
    - Проверить корректное отображение смешанного русско-казахского контента
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [ ]* 10.2 Написать property test для сохранения языка пользовательского контента
    - **Property 18: User Content Language Preservation**
    - **Validates: Requirements 11.1, 11.2**
  
  - [x] 10.3 Обеспечить UTF-8 encoding для хранения контента
    - Проверить что база данных использует UTF-8
    - Проверить корректное хранение кириллицы
    - _Requirements: 11.5_

- [x] 11. Реализовать миграцию и обратную совместимость
  - [x] 11.1 Создать логику миграции существующих языковых предпочтений
    - Распознавать существующие предпочтения пользователей
    - Мигрировать 'en' предпочтения в 'ru' для консистентности
    - Устанавливать 'ru' по умолчанию для пользователей без предпочтений
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [x] 11.2 Обеспечить обратную совместимость API
    - Проверить что существующие API контракты не нарушены
    - Проверить что запросы без language параметра работают с дефолтом 'ru'
    - _Requirements: 12.4, 12.5_

- [x] 12. Final checkpoint - Комплексное тестирование
  - [x] 12.1 Выполнить end-to-end тестирование смены языка
    - Переключить язык на казахский в Settings
    - Проверить обновление всех UI элементов
    - Проверить сохранение в localStorage
    - Перезагрузить страницу и проверить персистентность
  
  - [x] 12.2 Протестировать генерацию AI контента на казахском
    - Сгенерировать summary на казахском
    - Сгенерировать quiz на казахском
    - Выполнить chat на казахском
    - Проверить evaluation на казахском
  
  - [x] 12.3 Проверить корректность всех переводов
    - Вручную проверить качество казахских переводов
    - Проверить грамматическую корректность
    - Проверить соответствие образовательной терминологии
  
  - [x] 12.4 Убедиться что все тесты проходят
    - Запустить все unit тесты
    - Запустить все property тесты
    - Запустить integration тесты
    - Проверить отсутствие регрессий

## Notes

- Задачи, отмеченные `*`, являются опциональными и могут быть пропущены для более быстрого MVP
- Каждая задача ссылается на конкретные требования для отслеживаемости
- Checkpoints обеспечивают инкрементальную валидацию
- Property тесты валидируют универсальные свойства корректности
- Unit тесты валидируют конкретные примеры и граничные случаи
- Все AI-related задачи требуют ручной проверки качества генерируемого контента на казахском языке

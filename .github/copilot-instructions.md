# EduStream AI Agent Instructions

## Project Overview
EduStream is a virtual teaching assistant platform with FastAPI backend (Python 3.11) and Vite+React+TypeScript frontend. Backend deployed via Docker Compose on production server (94.131.85.176), frontend auto-deploys to Vercel on git push to main.

## Critical Architecture Patterns

### Backend Structure
- **Active endpoints**: Use `*_swagger.py` files in `app/api/v1/endpoints/` (e.g., `ai_swagger.py`, `materials_swagger.py`)
- **Legacy files**: `ai.py`, `materials.py`, `analytics.py`, `ocr.py` are NOT imported in `router.py` - ignore them
- **Models**: All use UUID primary keys, timestamps (created_at/updated_at), and proper relationships
- **Course model**: Recently added (migration 004) - Materials and OCRResults link to courses via UUID foreign keys with `ondelete='SET NULL'`

### Frontend Structure (EduStream-Frontend/)
- **State management**: React Context API, not Redux. See `context/` for CourseContext, UserContext, LanguageContext
- **API layer**: All backend calls go through `lib/api.ts` services (AuthService, CourseService, AIService, etc.) - NEVER use fetch() directly in components
- **Types**: All interfaces defined in `types.ts` - Course, Material, Quiz, User, etc.
- **Styling**: Tailwind CSS utility-first, Material Symbols Outlined icons

## Development Workflows

### Backend Changes
```bash
# 1. Edit Python files locally
# 2. Upload to server
scp -i ssh-key-1770638448815 app/path/to/file.py baltabek@94.131.85.176:~/edustream/app/path/to/file.py
# 3. Restart container
ssh -i ssh-key-1770638448815 baltabek@94.131.85.176 "cd edustream && docker compose restart app"
# 4. Check logs
ssh -i ssh-key-1770638448815 baltabek@94.131.85.176 "cd edustream && docker compose logs app --tail 50"
```

### Frontend Changes
```bash
cd EduStream-Frontend
git add .
git commit -m "fix: description"
git push origin main  # Triggers Vercel auto-deploy (~2 min)
```

### Database Migrations
```bash
# 1. Create migration locally
alembic revision --autogenerate -m "description"
# 2. Upload to server
scp -i ssh-key-1770638448815 alembic/versions/00X_*.py baltabek@94.131.85.176:~/edustream/alembic/versions/
# 3. Apply on server
ssh -i ssh-key-1770638448815 baltabek@94.131.85.176 "cd edustream && docker compose exec app alembic upgrade head"
```

## Common Pitfalls & Solutions

### Backend
1. **Missing imports**: When adding new schemas, import them explicitly in endpoint files:
   ```python
   from app.schemas.swagger_schemas import Material, MaterialUpdate, MaterialUploadResponse
   ```
2. **CORS issues**: Production allows `https://edu-stream-mu.vercel.app` - update `.env` CORS_ORIGINS if needed
3. **UUID types**: Use `get_uuid_type()` helper in migrations for PostgreSQL/SQLite compatibility
4. **Relationship syntax**: Always close parentheses properly:
   ```python
   course = relationship("Course", back_populates="materials")  # NOT: ...materials"
   ```

### Frontend
1. **Variable naming**: Context exports may use aliases (e.g., `loading: loadingCourses`) - check destructuring carefully
2. **Course context**: `selectedCourse` is now a Course object, not a string. Use `selectedCourse.id` for API calls
3. **Trailing slashes**: Backend expects `/materials/` WITH trailing slash - don't use `/materials`
4. **API errors**: 502 Bad Gateway = backend container crashed. Check docker logs immediately

## Testing & Verification

### Test user creation
```bash
# Login endpoint uses form-data with "username" field (not "email")
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher@example.com&password=yourpassword"
```

### Check backend health
```bash
# Quick status
ssh -i ssh-key-1770638448815 baltabek@94.131.85.176 "cd edustream && docker compose ps"
# App should show "Up" status, db should show "(healthy)"
```

### Frontend build errors
- Look for `loading is not defined` → check Context API destructuring aliases
- `Unexpected "."` or broken JSX → incomplete search/replace likely corrupted file structure
- Import errors → ensure types are exported from `types.ts`

## Key Files Reference

- Backend entry: `app/main.py` (lifespan events, CORS config)
- API router: `app/api/v1/router.py` (includes only *_swagger.py endpoints)
- Models: `app/models/models.py` (Course, Material, User, OCRResult with UUIDs)
- Schemas: `app/schemas/swagger_schemas.py` (Pydantic validation)
- Frontend API: `EduStream-Frontend/lib/api.ts` (service layer pattern)
- Migration versions: `alembic/versions/` (004 is latest - added Course model)

## AI Integration Note
Project currently configured for OpenAI API, but can be adapted to OpenRouter.ai by modifying:
- `app/services/ai_service.py` (change base URL and headers)
- `app/core/config.py` (rename OPENAI_API_KEY to OPENROUTER_API_KEY)

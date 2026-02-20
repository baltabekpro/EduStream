# EduStream AI Agent Instructions

## Big picture
- Monorepo with two codebases: backend in root (`app/`) and frontend in `EduStream-Frontend/`.
- Backend is FastAPI + SQLAlchemy + Alembic; frontend is Vite + React + TypeScript + Tailwind.
- Production flow: backend is manually synced to server (`94.131.85.176`, Docker Compose), frontend auto-deploys to Vercel on push.

## Architecture that matters
- API router (`app/api/v1/router.py`) includes active endpoints:
   `auth.py`, `dashboard.py`, `users.py`, `courses.py`, `share.py`, and `*_swagger.py` files.
- For AI/materials/analytics/OCR, use `*_swagger.py` as source of truth (`ai_swagger.py`, `materials_swagger.py`, `analytics_swagger.py`, `ocr_swagger.py`).
- Legacy non-swagger endpoint files (`ai.py`, `materials.py`, `analytics.py`, `ocr.py`) are not wired in router.
- Core teacher flows are cross-feature:
   material -> AI generation -> share link -> student submit -> OCR/analytics/journal.

## Backend conventions
- Models are in `app/models/models.py`; IDs are UUID-based and timestamps are required in most entities.
- Course-aware features filter by `course_id` (see `materials_swagger.py`, `analytics_swagger.py`, `share.py`).
- Config uses `pydantic-settings` (`app/core/config.py`) and Gemini keys (`GEMINI_API_KEY`, `GEMINI_MODEL`).
- Keep response shapes stable for frontend service adapters in `EduStream-Frontend/lib/api.ts`.

## Frontend conventions
- Routing uses `HashRouter` in `EduStream-Frontend/App.tsx` (`/#/...` URLs are expected).
- Role-gated views are implemented via `RoleRoute`; respect teacher/admin vs student route separation.
- Use service layer only (`lib/api.ts`) from pages/components; types live in `types.ts`.
- `selectedCourse` from context is an object, use `selectedCourse.id` for API calls.

## Critical workflows
- Backend local run: `uvicorn app.main:app --reload`.
- Backend tests: `pytest` (see `tests/`, SQLite test DB via `tests/conftest.py`).
- Frontend build check: run `npm run build` inside `EduStream-Frontend/`.
- Backend deploy pattern:
   1) copy changed files with `scp` to `~/edustream/`
   2) `docker compose restart app`
   3) inspect `docker compose logs app --tail 50`
- Frontend deploy pattern: commit/push in `EduStream-Frontend` repo (`main` -> Vercel).

## Repo-specific pitfalls
- `EduStream-Frontend` is its own git repo (nested); push frontend changes there, not only in root repo.
- `/materials/` expects trailing slash in many client calls; keep existing endpoint strings consistent.
- If UI suddenly shows 404/502, check backend container logs first (often stale server code or crash).
- Share/assignment flows depend on `resourceType` (`quiz` vs `material`) and short-code format validation in `share.py`.

## Key files to inspect first
- Backend: `app/api/v1/router.py`, `app/api/v1/endpoints/share.py`, `app/api/v1/endpoints/analytics_swagger.py`, `app/services/ai_service.py`, `app/core/config.py`.
- Frontend: `EduStream-Frontend/App.tsx`, `EduStream-Frontend/lib/api.ts`, `EduStream-Frontend/pages/Assignments.tsx`, `EduStream-Frontend/pages/SharedQuiz.tsx`, `EduStream-Frontend/pages/QuizResults.tsx`.

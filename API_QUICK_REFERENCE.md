# EduStream API Quick Reference

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload

# Access documentation
http://localhost:8000/docs
```

## API Base URL

**Local**: `http://localhost:8000/api/v1`  
**Production**: `https://api.edustream.app/v1`

## Authentication

All endpoints (except `/auth/login`) require JWT Bearer token:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher@example.com", "password": "password123"}'

# Response
{
  "token": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "teacher@example.com",
    "role": "teacher"
  }
}

# Use token in subsequent requests
curl -H "Authorization: Bearer eyJhbGc..." \
  http://localhost:8000/api/v1/dashboard/overview?courseId=9A
```

## Endpoint Summary

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/overview?courseId={id}` | Teacher's main dashboard |

### AI Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ai/templates` | Quiz template gallery |
| POST | `/ai/chat` | RAG chat with material context |
| POST | `/ai/smart-action` | Quick text transformations |
| POST | `/ai/generate-quiz` | Generate quiz with difficulty control |
| POST | `/ai/regenerate-block` | Regenerate single question |
| GET | `/ai/sessions` | Chat history |

### OCR
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ocr/results/{id}` | Get OCR result details |
| PATCH | `/ocr/results/{id}` | Manual correction |
| POST | `/ocr/batch-approve` | Batch approval |

### Materials
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/materials` | List all materials |
| POST | `/materials` | Upload file (multipart/form-data) |
| GET | `/materials/{id}` | Get material content |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/performance?courseId={id}` | Full analytics data |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Current user profile |
| PATCH | `/users/me` | Update profile/settings |

### Share
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/share/create` | Create public sharing link |

## Common Request Examples

### Generate Quiz
```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-quiz \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "materialId": "material-uuid",
    "difficulty": "hard",
    "count": 10,
    "type": "mcq"
  }'
```

### Upload Material
```bash
curl -X POST http://localhost:8000/api/v1/materials \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf" \
  -F "courseId=9A"
```

### Smart Action
```bash
curl -X POST http://localhost:8000/api/v1/ai/smart-action \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Митохондрия является энергетической станцией клетки",
    "action": "simplify",
    "context": "Биология, 9 класс"
  }'
```

### Batch OCR Approval
```bash
curl -X POST http://localhost:8000/api/v1/ocr/batch-approve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["result1-uuid", "result2-uuid"]
  }'
```

## Response Formats

### Success Response
```json
{
  "id": "uuid",
  "data": {...}
}
```

### Error Response
```json
{
  "code": 422,
  "message": "Validation Error",
  "details": {
    "field_name": "Error description"
  }
}
```

## Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PATCH |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Async processing started |
| 207 | Multi-Status | Partial batch success |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | No permission |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | AI service down |
| 504 | Timeout | Request took too long |

## Difficulty Levels

When generating quizzes, difficulty affects question complexity:

- **easy**: Basic understanding, simple vocabulary
- **medium**: Application of concepts, moderate vocabulary  
- **hard**: Analysis and synthesis, complex vocabulary

## Question Types

- **mcq**: Multiple choice (4 options)
- **open**: Open-ended response
- **boolean**: True/False

## Smart Actions

- **explain**: Simple explanation for students
- **simplify**: Reduce text complexity
- **translate**: Translate to English
- **summarize**: Create brief summary

## Material Statuses

- **processing**: Upload in progress
- **ready**: Available for use
- **error**: Processing failed

## OCR Confidence

- **High**: Accurate recognition
- **Low**: Uncertain, needs review (highlighted yellow in UI)

## Environment Variables

```bash
# Required
DATABASE_URL=sqlite:///./edustream.db
SECRET_KEY=your-secret-key

# Optional (uses mocks if not set)
OPENAI_API_KEY=sk-...

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## Database Migration

```bash
# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check version
alembic current
```

## Testing Without OpenAI API

The system provides mock responses when `OPENAI_API_KEY` is not set, allowing full testing without incurring API costs.

## Interactive Documentation

Visit `http://localhost:8000/docs` for:
- Complete API reference
- Try-it-out functionality
- Schema definitions
- Authentication testing

## Support

For issues and questions:
1. Check SWAGGER_IMPLEMENTATION.md for detailed docs
2. Review swagger.yml for API contract
3. Visit /docs for interactive testing
4. Check logs in logs/app.log

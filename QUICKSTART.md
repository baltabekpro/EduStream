# EduStream Quick Start Guide

This guide will help you quickly set up and run the EduStream API.

## Prerequisites

- Python 3.10 or higher
- PostgreSQL (for production) or SQLite (for development)
- (Optional) Docker and Docker Compose

## Quick Start with SQLite (Development)

1. **Clone the repository**
```bash
git clone https://github.com/Barleennn/EduStream.git
cd EduStream
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
# The default .env uses SQLite, so no additional configuration needed for testing
```

5. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

## Quick Start with Docker

1. **Clone and configure**
```bash
git clone https://github.com/Barleennn/EduStream.git
cd EduStream
cp .env.example .env
```

2. **Start with Docker Compose**
```bash
docker-compose up -d
```

The API will be available at: http://localhost:8000

## Testing the API

### 1. Register a Teacher
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "password": "SecurePassword123",
    "role": "teacher"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "password": "SecurePassword123"
  }'
```

Save the `access_token` from the response.

### 3. Upload a Material
```bash
curl -X POST "http://localhost:8000/api/v1/materials/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### 4. Generate Summary
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "MATERIAL_UUID_FROM_UPLOAD"
  }'
```

### 5. Generate Quiz
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-quiz" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "MATERIAL_UUID_FROM_UPLOAD",
    "num_questions": 5,
    "difficulty": "medium"
  }'
```

### 6. View Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v
```

## API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Structure

```
EduStream/
├── app/
│   ├── api/v1/endpoints/  # API endpoints
│   ├── core/              # Configuration and security
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── tests/                 # Test files
├── alembic/               # Database migrations
├── docker-compose.yml     # Docker services
├── Dockerfile             # Application container
└── requirements.txt       # Python dependencies
```

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/materials/upload` | Upload PDF/DOCX |
| GET | `/api/v1/materials/{id}` | Get material |
| POST | `/api/v1/ai/generate-summary` | Generate summary |
| POST | `/api/v1/ai/generate-quiz` | Generate quiz |
| POST | `/api/v1/ocr/recognize` | OCR text recognition |
| GET | `/api/v1/analytics/dashboard` | Get dashboard stats |

## Configuration

Edit `.env` file to configure:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Vision API credentials

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running (if using PostgreSQL)
- Check `DATABASE_URL` in `.env`

### OpenAI API Error
- Set `OPENAI_API_KEY` in `.env`
- The API will use mock responses if no key is provided

### Port Already in Use
- Change `PORT` in `.env` or use different port with uvicorn:
```bash
uvicorn app.main:app --port 8080
```

## Next Steps

1. Configure production database (PostgreSQL)
2. Set up proper API keys for OpenAI and Google Vision
3. Configure CORS for your frontend
4. Deploy to production server
5. Set up monitoring and logging

## Support

For issues and questions, please open an issue on GitHub.

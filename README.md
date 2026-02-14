# EduStream - Virtual Teaching Assistant API

EduStream is a powerful backend API for a virtual teaching assistant platform that helps teachers manage educational materials, generate AI-powered content, perform OCR on student work, and track student analytics.

## 🚀 Features

- **Authentication**: JWT-based authentication with access and refresh tokens
- **Material Management**: Upload and process PDF/DOCX files with automatic text extraction
- **AI-Powered Generation**: 
  - Generate summaries and glossaries from educational materials
  - Create quiz questions automatically with configurable difficulty
- **OCR Processing**: Recognize text from images of student work
- **Analytics Dashboard**: Track student performance and visualize knowledge maps
- **Privacy-First**: No biometric data storage, anonymized student data
- **Asynchronous**: Built for efficient handling of long-running AI/OCR operations
- **API Documentation**: Auto-generated Swagger UI at `/docs`

## 📋 Technology Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT with bcrypt password hashing
- **AI Integration**: OpenAI API (GPT-3.5-turbo)
- **OCR**: Tesseract OCR with Russian and English support
- **File Processing**: pypdf, python-docx
- **Testing**: Pytest with async support
- **Containerization**: Docker & Docker Compose

## 🏗️ Project Structure

```
EduStream/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # Authentication endpoints
│   │   │   │   ├── materials.py     # Material management
│   │   │   │   ├── ai.py            # AI generation endpoints
│   │   │   │   ├── ocr.py           # OCR processing
│   │   │   │   └── analytics.py     # Analytics endpoints
│   │   │   └── router.py            # API router
│   │   └── dependencies.py          # Auth dependencies
│   ├── core/
│   │   ├── config.py                # Configuration
│   │   ├── database.py              # Database setup
│   │   └── security.py              # Security utilities
│   ├── models/
│   │   └── models.py                # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py               # Pydantic schemas
│   ├── services/
│   │   ├── ai_service.py            # AI integration
│   │   ├── ocr_service.py           # OCR processing
│   │   └── file_processor.py        # File handling
│   └── main.py                      # FastAPI application
├── alembic/
│   ├── versions/                    # Migration scripts
│   └── env.py                       # Alembic environment
├── tests/
│   ├── conftest.py                  # Test configuration
│   ├── test_main.py                 # Main app tests
│   └── test_auth.py                 # Auth tests
├── docker-compose.yml               # Docker services
├── Dockerfile                       # Application container
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── README.md
```

## 🗄️ Database Schema

### Users
- Teachers and admins with JWT authentication
- Email/password login with bcrypt hashing

### Materials
- Educational content with extracted text
- AI-generated summaries and glossaries
- File storage references

### Quizzes
- AI-generated questions (MCQ and Open)
- Linked to materials

### StudentResults
- Performance tracking by student identifier
- Weak topics identification
- Score percentages

### ChatLogs
- Session-based chat logging
- AI-analyzed FAQ and activity reports

## 🔧 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL
- Docker & Docker Compose (optional)

### Local Development Setup

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

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup database**
```bash
# Create PostgreSQL database
createdb edustream_db

# Run migrations
alembic upgrade head
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env if needed
```

2. **Start services**
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /register` - Register new teacher/admin
- `POST /login` - Login and get JWT tokens
- `POST /refresh` - Refresh access token

### Materials (`/api/v1/materials`)

- `POST /upload` - Upload PDF/DOCX file
- `GET /{material_id}` - Get material by ID
- `GET /` - List all materials

### AI Generation (`/api/v1/ai`)

- `POST /generate-summary` - Generate summary and glossary
- `POST /generate-quiz` - Generate quiz questions

### OCR (`/api/v1/ocr`)

- `POST /recognize` - Recognize text from image

### Analytics (`/api/v1/analytics`)

- `GET /dashboard` - Get dashboard statistics
- `GET /knowledge-map` - Get knowledge map data

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/edustream_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Upload limits and public frontend URL for share links
MAX_UPLOAD_SIZE=10485760
FRONTEND_BASE_URL=https://edu-stream-mu.vercel.app

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 📖 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Usage Examples

### 1. Register and Login

```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "password": "SecurePassword123",
    "role": "teacher"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "password": "SecurePassword123"
  }'
```

### 2. Upload Material

```bash
curl -X POST "http://localhost:8000/api/v1/materials/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### 3. Generate Summary

```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "MATERIAL_UUID"
  }'
```

### 4. Generate Quiz

```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-quiz" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "MATERIAL_UUID",
    "num_questions": 5,
    "difficulty": "medium"
  }'
```

## 🛡️ Security Features

- **Password Hashing**: Bcrypt for secure password storage
- **JWT Tokens**: Separate access and refresh tokens
- **CORS**: Configurable CORS origins
- **Input Validation**: Pydantic schemas for all endpoints
- **SQL Injection Protection**: SQLAlchemy ORM
- **Privacy-First**: No biometric data storage

## 📝 Logging

Logs are configured with Loguru:
- Console output with color formatting
- File rotation (500 MB)
- 10-day retention
- Logs stored in `logs/app.log`

## 🚧 Development

### Code Style

Follow PEP 8 Python style guidelines.

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📄 License

This project is part of the EduStream platform.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions, please open an issue in the GitHub repository.
# 🍽️ MenuBox AI

**AI-powered restaurant menu recommendations based on review analysis and personal preferences.**

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS, React Router
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL
- **AI:** Anthropic Claude API

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (with pgAdmin)

### 1. Database Setup (pgAdmin)

1. Open pgAdmin and connect to your PostgreSQL server
2. Right-click **Databases** → **Create** → **Database**
3. Name it `menubox_ai` and click Save
4. Click on `menubox_ai` → **Query Tool**
5. Copy/paste contents of `database/schema.sql` and run (F5)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run server
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API Docs at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at: http://localhost:5173

## Environment Variables

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/menubox_ai
JWT_SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key  # Optional, for AI recommendations
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Sign in |
| GET | /api/user/me | Get current user |
| GET | /api/user/preferences | Get preferences |
| PUT | /api/user/preferences | Update preferences |
| POST | /api/menu/upload | Upload menu image |
| POST | /api/menu/search | Search restaurant |
| POST | /api/recommendations/generate | Get AI recommendations |
| GET | /api/recommendations/{id} | Get recommendation by ID |

## Project Structure

```
menubox-ai/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic (AI, etc.)
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
└── database/
    └── schema.sql
```

## Features

- ✅ User authentication (JWT)
- ✅ User preferences management
- ✅ Restaurant search
- ✅ Menu image upload
- ✅ AI-powered recommendations (Claude)
- 🔲 Review scraping
- 🔲 OCR for menu images

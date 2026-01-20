# 🍽️ MenuBox AI

AI-powered restaurant menu recommendations based on your dietary preferences.

## Features
- 📸 Upload menu photos for instant recommendations
- 🔍 Search restaurants by name
- ⚙️ Set dietary preferences & allergies
- 🤖 Powered by Claude AI

## Tech Stack
- **Frontend**: React + Vite + Tailwind
- **Backend**: FastAPI + PostgreSQL
- **AI**: Anthropic Claude
- **Email**: Brevo

## Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Made by Advay
```

**2. Add `.gitignore`** (root of repo, if you don't have one):
```
# Python
__pycache__/
*.pyc
.env
venv/

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
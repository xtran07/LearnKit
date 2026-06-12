# Interview Prep Tracker

Tracks your resume, generates study topics from it, lets you manage topics, generates/grades
interview questions with free-tier LLMs (Gemini, Groq), and tracks your progress per topic.

## Stack

- **Frontend**: React + Vite + Tailwind CSS (`frontend/`)
- **Backend**: FastAPI + SQLAlchemy (async) + asyncpg (`backend/`)
- **Database**: Neon Postgres
- **File storage**: Supabase Storage (resume files)
- **LLMs**: Gemini (free tier, primary) and Groq (free tier, secondary)

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # fill in DATABASE_URL, SUPABASE_*, GEMINI_API_KEY, GROQ_API_KEY
uvicorn app.main:app --reload
```

Tables are created automatically on startup via `Base.metadata.create_all`.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env  # set VITE_API_BASE_URL if backend isn't on localhost:8000
npm run dev
```

## Features

- **Resume**: upload a PDF/TXT/MD resume. It's stored in Supabase Storage and its text is
  extracted and saved. Click "Suggest Topics" to have an LLM propose study topics from the
  resume content.
- **Topics**: add/rename/exclude/delete topics. Status cycles active → excluded → mastered.
- **Study**: pick a topic, generate questions (with ideal answers) via Gemini or Groq, answer
  them, and get an LLM-graded score + feedback. If the generated questions aren't good enough,
  use "Get Prompt for Other Chatbots" to copy a ready-made prompt into ChatGPT/Claude/etc., then
  add the better questions manually via "Add Question Manually".
- **Progress**: per-topic summary of total questions, attempted questions, and average score.

## Deployment (free tier)

- Frontend → Vercel
- Backend → Render
- Database → Neon
- File storage → Supabase Storage

Set the corresponding environment variables (`DATABASE_URL`, `SUPABASE_*`, `GEMINI_API_KEY`,
`GROQ_API_KEY`, `FRONTEND_ORIGIN`) on Render, and `VITE_API_BASE_URL` on Vercel pointing at the
Render backend URL.

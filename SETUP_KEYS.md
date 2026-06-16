# API Keys & Environment Setup

Instructions for obtaining each value needed in `backend/.env` and `frontend/.env`
(copy from the `.env.example` files in each folder). Never commit `.env` files or
paste real keys into code — only into `.env` (local) or your hosting platform's
environment variable settings (deployed).

## 1. `DATABASE_URL` (Neon Postgres)

1. Go to https://neon.tech -> sign in/sign up (free tier).
2. Create a project (any region close to you, e.g. AWS Singapore for Hyderabad).
3. In the project dashboard, go to **Connection Details** -> select the "Pooled connection" string.
4. It looks like: `postgresql://user:password@ep-xxxx.ap-southeast-1.aws.neon.tech/dbname?sslmode=require`
5. Convert it to the async driver format used by this backend:
   `postgresql+asyncpg://user:password@ep-xxxx.ap-southeast-1.aws.neon.tech/dbname?ssl=require`
   (replace `postgresql://` -> `postgresql+asyncpg://`, and `sslmode=require` -> `ssl=require`)
6. **Important**: if Neon's connection string also includes `&channel_binding=require`, remove
   that part entirely. `asyncpg` does not accept `channel_binding` as a connect parameter and
   will fail at startup with `TypeError: connect() got an unexpected keyword argument
   'channel_binding'`.

## 2. Supabase Storage (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`)

1. Go to https://supabase.com -> create a free project.
2. **SUPABASE_URL**: Project Settings -> API -> "Project URL" (e.g. `https://xxxx.supabase.co`)
3. **SUPABASE_SERVICE_KEY**: same page -> "Project API keys" -> copy the **`service_role`** key
   (NOT the `anon` key -- service_role is needed for server-side uploads). Keep this secret,
   never expose it to the frontend.
4. **SUPABASE_BUCKET**: go to Storage -> create a new bucket (e.g. name it `resumes`). Set it
   to private (the backend uploads/serves via the service key). Then `SUPABASE_BUCKET=resumes`.

## 3. `GEMINI_API_KEY` (Google Gemini, free tier)

1. Go to https://aistudio.google.com/apikey (Google AI Studio).
2. Sign in with your Google account -> "Create API key".
3. Copy the key -- it's free-tier usable immediately, no billing setup required for the free quota.

## 4. `GROQ_API_KEY` (Groq, free tier)

1. Go to https://console.groq.com/keys.
2. Sign in/sign up -> "Create API Key".
3. Copy the key -- Groq's free tier requires no payment info.

## 5. `OPENROUTER_API_KEY` (OpenRouter, free tier)

1. Go to https://openrouter.ai -> sign in/sign up (free).
2. Go to https://openrouter.ai/keys -> "Create Key".
3. Copy the key -- the curated models used by this app (`meta-llama/llama-3.3-70b-instruct:free`
   and `deepseek/deepseek-chat-v3.1:free`) are free-tier and require no payment info.

## 6. Frontend `VITE_API_BASE_URL`

- Local dev: `http://localhost:8000`
- After deploying backend to Render: your Render service URL, e.g. `https://your-app.onrender.com`

---

## Deployment

- **Render** (backend): Dashboard -> your service -> Environment -> add `DATABASE_URL`,
  `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`, `GEMINI_API_KEY`, `GROQ_API_KEY`,
  `OPENROUTER_API_KEY`, `FRONTEND_ORIGIN` (your Vercel URL).
- **Vercel** (frontend): Project Settings -> Environment Variables -> add `VITE_API_BASE_URL`
  (your Render backend URL).

---

## Deploy Backend to Render

1. Push your code to GitHub (if not already):
   ```bash
   git add .
   git commit -m "Initial scaffold"
   git push
   ```
2. Go to https://render.com -> sign in with GitHub.
3. "New +" -> "Web Service" -> select your `LearnKit` repo.
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Add environment variables (Environment tab): `DATABASE_URL`, `SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`, `GEMINI_API_KEY`, `GROQ_API_KEY`,
   `OPENROUTER_API_KEY`. Leave `FRONTEND_ORIGIN` as `http://localhost:5173` for now -- update
   it after deploying the frontend (step below).
6. Click "Create Web Service". Render builds and gives you a URL like
   `https://learnkit-api.onrender.com`.

Note: Render's free tier spins down after inactivity, so the first request after idling
may take ~30-60 seconds to respond.

## Deploy Frontend to Vercel

1. Go to https://vercel.com -> sign in with GitHub.
2. "Add New..." -> "Project" -> select your `LearnKit` repo -> "Import".
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (should auto-detect)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
4. Add environment variable: `VITE_API_BASE_URL` = your Render backend URL
   (e.g. `https://learnkit-api.onrender.com`).
5. Click "Deploy". Vercel builds and gives you a URL like `https://learnkit-xxxx.vercel.app`.

## Final step: connect the two

Go back to Render -> your backend service -> Environment -> update `FRONTEND_ORIGIN` to your
Vercel URL (e.g. `https://learnkit-xxxx.vercel.app`), then redeploy the backend so CORS allows
requests from your live frontend.

### Recommended order
1. Deploy backend to Render first (get its URL).
2. Deploy frontend to Vercel using that URL for `VITE_API_BASE_URL`.
3. Update `FRONTEND_ORIGIN` on Render with the Vercel URL and redeploy.

---

## Login with Google (Supabase Auth)

### 1. Frontend Supabase keys (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`)

1. In your Supabase project: Project Settings -> API.
2. **VITE_SUPABASE_URL** = "Project URL" (same value as `SUPABASE_URL`).
3. **VITE_SUPABASE_ANON_KEY** = "Project API keys" -> the **`anon` / `public`** key (safe to
   expose in the frontend -- do NOT use the `service_role` key here).

### 2. Backend JWT secret (`SUPABASE_JWT_SECRET`)

1. Same Project Settings -> API page -> "JWT Settings" -> copy the **JWT Secret**.
2. This lets FastAPI verify the access tokens Supabase issues after login.

### 3. Create a Google OAuth Client

1. Go to https://console.cloud.google.com/ -> create/select a project.
2. "APIs & Services" -> "OAuth consent screen" -> configure (External, add your email as a
   test user if still in testing mode).
3. "APIs & Services" -> "Credentials" -> "Create Credentials" -> "OAuth client ID" ->
   Application type: **Web application**.
4. Under "Authorized redirect URIs", add:
   `https://<your-project-ref>.supabase.co/auth/v1/callback`
   (find `<your-project-ref>` in your Supabase project URL).
5. Copy the generated **Client ID** and **Client Secret**.

### 4. Enable Google provider in Supabase

1. Supabase dashboard -> Authentication -> Providers -> Google -> enable it.
2. Paste the Client ID and Client Secret from step 3. Save.

### 5. Configure redirect URLs in Supabase

1. Authentication -> URL Configuration.
2. Set **Site URL** to your deployed frontend URL (e.g. `https://learnkit-xxxx.vercel.app`).
3. Add both `http://localhost:5173` and your Vercel URL to **Redirect URLs** so login works
   in local dev and production.

### 6. Add the new env vars everywhere

- `backend/.env` and Render: `SUPABASE_JWT_SECRET`
- `frontend/.env` and Vercel: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

### Note on existing data

The `resumes` and `topics` tables now have a required `user_id` column. If you already have
rows from before auth was added, either delete them (fresh start) or manually backfill
`user_id` with your Supabase user UUID (Authentication -> Users, after your first Google
login) before the app will show them again.

# 🍽️ MenuBox AI

**AI-powered restaurant menu recommendations based on review analysis and your personal taste.**

🔗 **Live:** https://menubox-ai.vercel.app · **Code:** https://github.com/advayiyer7/menubox-ai

A full-stack web app that helps you decide *what to actually order* at a restaurant. You tell it your dietary preferences once; then for any restaurant — searched by name or uploaded as a menu photo — it analyzes the menu against real customer reviews and your taste profile, and recommends the best dishes for *you*, with a match score and reasoning.

---

## What it does

1. **Create an account** — email + password, with email verification.
2. **Set your taste profile** — dietary restrictions (vegetarian, vegan, gluten-free…), favorite cuisines, disliked ingredients, spice level, price preference, and free-text notes.
3. **Get recommendations two ways:**
   - **Search a restaurant** by name/location → the app finds it on Google Places, pulls its menu and recent reviews, and ranks the best dishes for you.
   - **Upload a menu photo** → AI reads the menu (OCR), cross-references the dishes against Google reviews, and ranks them.
4. **See ranked picks** — each with a 0–100 **match score** and a one-line **reason** (e.g. *"Highly rated in reviews and fits your vegetarian + mild-spice preference"*). Dietary restrictions are treated as hard constraints — the AI never recommends something that violates them.

---

## How it works

### Architecture

```
┌──────────────┐    /api/*  (proxy)    ┌──────────────┐
│   Vercel     │ ────────────────────▶ │    Render    │
│  React + Vite│                       │   FastAPI    │
│  (frontend)  │ ◀──────────────────── │  (backend)   │
└──────────────┘                       └──────┬───────┘
                                              │
              ┌───────────────┬───────────────┼───────────────┐
              ▼               ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
       │    Neon    │  │  Anthropic │  │   Google   │  │   Brevo    │
       │ PostgreSQL │  │   Claude   │  │   Places   │  │  (email)   │
       └────────────┘  └────────────┘  └────────────┘  └────────────┘
```

The React frontend never talks to the AI/Google APIs directly — it calls its own `/api/*` routes, which Vercel transparently proxies to the FastAPI backend. **All API keys live only on the backend**, never in the browser.

### The recommendation pipeline

**Restaurant search flow:**
```
name + location
   → Google Places: find restaurant, get details + reviews
   → Claude (web search): find the restaurant's menu items
   → Claude: analyze Google reviews to find which dishes are praised
   → Claude: rank dishes against the user's taste profile + review signal
   → ranked picks (score + reasoning), saved to history
```

**Menu-photo flow:**
```
uploaded image(s)
   → Claude Vision (OCR): extract dish names, descriptions, prices
   → Google reviews: cross-reference those dishes for sentiment
   → Claude: rank against the user's taste profile
   → ranked picks
```

### Auth flow
Registration creates an **unverified** account and emails a verification link (via Brevo). Login is **blocked until the email is verified**. On login the backend issues a short-lived **JWT access token** plus a long-lived **refresh token** (stored server-side, revocable). The frontend transparently refreshes expired access tokens via an Axios interceptor.

---

## Tech stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 7, Tailwind CSS 4, React Router 7, Axios |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, Uvicorn |
| **Database** | PostgreSQL — Neon (serverless, prod) · Docker (local) |
| **AI** | Anthropic Claude (Sonnet 4.6) — recommendations, Vision OCR, web-search menu lookup, review sentiment analysis |
| **External APIs** | Google Places (search + reviews), Brevo (transactional email) |
| **Auth & security** | JWT (access + refresh), bcrypt password hashing, email verification, slowapi rate limiting, per-user daily quotas |
| **Hosting** | Vercel (frontend) · Render (backend) · Neon (database) — **all free tier** |

---

## Security & cost engineering

Because the app calls paid AI/Google APIs on behalf of any logged-in user, a naïve deployment could be abused into a huge bill. I built **three layers of defense**:

1. **IP rate limiting** (slowapi) on every expensive and auth endpoint — e.g. login `20/min`, restaurant search `20/hr`, recommendations `30/hr`, registration `10/hr` (stops brute-force, signup spam, and request floods).
2. **Durable per-user daily quotas** — a `usage_events` table records each billable AI action; a single account is capped per day (search 30, upload 30, recommend 50). Survives server restarts, unlike in-memory limits.
3. **Provider-level spend caps** — hard monthly/daily ceilings set in the Anthropic and Google Cloud consoles. The ultimate backstop: even if every app defense were bypassed, spend can't exceed these.

Other hardening:
- **No secrets in the repo** — `.env` is gitignored; all keys are injected as environment variables in the host dashboards. Keys live only server-side and never reach the client.
- **Tightened CORS** — explicit allowed origins + a Vercel-preview regex, restricted methods/headers.
- **Production config** — `DEBUG=False`, `APP_ENV=production` in the deployed backend.
- **Password security** — bcrypt hashing, 8-char minimum, never stored or logged in plaintext.

---

## Deployment & infrastructure

The app runs entirely on **free tiers** (~$0/month): Vercel + Render + Neon. The frontend and backend live in one repository (a monorepo), deployed from the same GitHub repo with different **root directories** (`menubox-ai/frontend` and `menubox-ai/backend`).

The backend **auto-creates its database schema from the SQLAlchemy models on startup**, so there are no manual migration steps — a fresh database is provisioned and populated on first boot.

---

## Engineering challenges solved

A realistic snapshot of the problems that came up taking this from "works on my machine" to "live on the internet":

- **Serverless Postgres (Neon) SNI requirement.** Neon routes to the right compute via TLS SNI, which the deployed `psycopg2` build wasn't sending — connections failed with *"Endpoint ID is not specified."* Fixed by parsing the endpoint ID from the connection URL and passing it explicitly (`options=endpoint=<id>`), so it works without hand-editing the connection string.
- **Python version pinning.** The host defaulted to a newer Python with no prebuilt wheels for the pinned dependencies, so the build tried to compile from source and failed. Pinned the runtime to the tested Python 3.12 via a `.python-version` file.
- **Database SSL.** Cloud Postgres requires SSL, but specifying `sslmode` twice (once in the URL, once in code) errors — made the SSL handling idempotent.
- **Keeping AI dependencies current.** The originally hard-coded Claude model was nearing retirement; migrated all AI calls to the current model so the app keeps working as models are deprecated.
- **Schema drift.** The hand-written SQL schema had silently fallen out of sync with the ORM models (missing columns/tables) — eliminated the drift by generating the schema from the models as the single source of truth.
- **Email deliverability.** Transactional email requires a verified sender and the correct API key *type* (REST API key vs. SMTP key) — and sending from a freemail address has DMARC/deliverability tradeoffs worth understanding.
- **Free-tier cold starts.** The free backend sleeps after inactivity, so the first request can lag or time out through the proxy — mitigated with an uptime ping to keep it warm.
- **Secrets hygiene.** Verified no API keys ever entered git history before publishing the repo.

---

## What I learned

- **Full-stack deployment end-to-end** — wiring a React SPA, a Python API, and a managed Postgres database across three hosting providers, including cross-service proxying and CORS.
- **Designing an LLM app that can't bankrupt you** — layering app-level rate limiting and per-user quotas with provider-level spend caps, and understanding why the provider cap is the only true guarantee.
- **The real-world quirks of serverless Postgres** (SNI, SSL, connection strings) and host build environments (Python versioning, wheels).
- **Secrets management** — keeping keys out of the repo and the browser, and using environment variables as the deployment boundary.
- **Prompt design for structured, constrained output** — getting an LLM to return ranked JSON that strictly respects hard constraints (dietary restrictions) while weighing soft signals (reviews, preferences).
- **Treating "it builds locally" and "it runs in production" as two different problems**, and reading deploy logs to diagnose the gap.

---

## Possible future improvements

- Deeper review mining (more than the handful of reviews the official API returns).
- A custom email-sending domain for better deliverability.
- Redis-backed rate limiting for multi-instance scaling.
- Caching of restaurant/menu lookups to cut API calls and latency.
- A richer preferences UI and shareable recommendation links.

---

## Run it locally

```bash
# Database (Docker)
docker run -d --name menubox-postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=menubox_ai -p 5432:5432 postgres:16

# Backend
cd backend
python -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env                               # then fill in keys
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev                                        # http://localhost:5173
```

Required keys in `backend/.env`: `ANTHROPIC_API_KEY` (core AI), `GOOGLE_PLACES_API_KEY` (search + reviews), `BREVO_API_KEY` (email). The app auto-creates all database tables on first run.

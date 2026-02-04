# 🚀 MenuBox AI - Complete Deployment Guide

## Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Render    │────▶│    Neon     │
│  (Frontend) │     │  (Backend)  │     │ (Database)  │
│   React     │     │   FastAPI   │     │ PostgreSQL  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │              ┌────┴────┐              │
       │              │  Brevo  │              │
       │              │ (Email) │              │
       │              └─────────┘              │
       │                                       │
   vercel.app                            neon.tech
```

---

## Part 1: Database (Neon) - Do This First!

### Step 1.1: Create Account
1. Go to https://neon.tech
2. Click "Sign Up" → Use GitHub
3. Authorize Neon

### Step 1.2: Create Project
1. Click "New Project"
2. Settings:
   - **Name**: `menubox-ai`
   - **Region**: `US East (Ohio)` or closest to you
3. Click "Create Project"

### Step 1.3: Get Connection String
1. On the dashboard, find "Connection string"
2. Click the copy button
3. It looks like:
   ```
   postgresql://username:password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. **Save this! You'll need it for Render.**

### Step 1.4: Create Tables
1. Click "SQL Editor" in left sidebar
2. Paste this entire SQL and click "Run":

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Preferences table
CREATE TABLE preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dietary_restrictions TEXT[] DEFAULT '{}',
    favorite_cuisines TEXT[] DEFAULT '{}',
    allergies TEXT[] DEFAULT '{}',
    custom_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    device_info VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Restaurants table
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    google_place_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Menu items table
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    price VARCHAR(50),
    category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendations table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id UUID REFERENCES restaurants(id),
    recommendations JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_menu_items_restaurant ON menu_items(restaurant_id);
```

3. You should see "Query executed successfully"

✅ **Database done!**

---

## Part 2: Backend (Render)

### Step 2.1: Create Account
1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub

### Step 2.2: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account if not already
3. Find and select your `menubox-ai` repo
4. Click **"Connect"**

### Step 2.3: Configure Service
Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `menubox-api` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

### Step 2.4: Add Environment Variables
Scroll down to "Environment Variables" and add each one:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://...` (paste your Neon connection string) |
| `JWT_SECRET_KEY` | Click "Generate" or make a random 64-character string |
| `ANTHROPIC_API_KEY` | `sk-ant-...` (your Claude API key) |
| `BREVO_API_KEY` | `xkeysib-...` (your Brevo key) |
| `GOOGLE_PLACES_API_KEY` | `AIza...` (your Google key) |
| `YELP_API_KEY` | Your Yelp key (optional) |
| `FRONTEND_URL` | `https://menubox-ai.vercel.app` (update after Vercel deploy) |
| `FROM_EMAIL` | `noreply@menubox.ai` |

### Step 2.5: Deploy
1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. Watch the logs for errors

### Step 2.6: Verify
Once deployed, you'll get a URL like:
```
https://menubox-api.onrender.com
```

Test it:
- Visit `https://menubox-api.onrender.com/health`
- Should see: `{"status": "healthy", "version": "1.0.0"}`

✅ **Backend done!**

---

## Part 3: Frontend (Vercel)

### Step 3.1: Create Account
1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"

### Step 3.2: Import Project
1. Click **"Add New..."** → **"Project"**
2. Find your `menubox-ai` repo
3. Click **"Import"**

### Step 3.3: Configure Project
| Setting | Value |
|---------|-------|
| **Framework Preset** | `Vite` |
| **Root Directory** | Click "Edit" → Select `frontend` |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `dist` (default) |

### Step 3.4: Update vercel.json
Make sure `frontend/vercel.json` has your Render URL:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://menubox-api.onrender.com/api/:path*"
    }
  ]
}
```

**Important:** Replace `menubox-api.onrender.com` with YOUR actual Render URL!

### Step 3.5: Deploy
1. Click **"Deploy"**
2. Wait 2-3 minutes
3. You'll get a URL like:
   ```
   https://menubox-ai.vercel.app
   ```

✅ **Frontend done!**

---

## Part 4: Connect Everything

### Step 4.1: Update Render with Vercel URL
1. Go to Render dashboard
2. Click on your `menubox-api` service
3. Go to **"Environment"**
4. Update `FRONTEND_URL` to your actual Vercel URL:
   ```
   https://menubox-ai.vercel.app
   ```
5. Click "Save Changes"
6. Render will auto-redeploy

### Step 4.2: Update vercel.json (if needed)
If your Render URL is different, update `frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-ACTUAL-RENDER-URL.onrender.com/api/:path*"
    }
  ]
}
```
Then push to GitHub - Vercel will auto-redeploy.

---

## Part 5: Test Everything! 🧪

### Test 1: Health Check
```
https://your-api.onrender.com/health
```
✅ Should return `{"status": "healthy"}`

### Test 2: Registration
1. Go to your Vercel URL
2. Click "Sign Up"
3. Enter email + password
4. Should go to "Check your email" page

### Test 3: Email Verification
1. Check your inbox (and spam!)
2. Click verification link
3. Should see "Email verified!"

### Test 4: Login
1. Go to login page
2. Enter credentials
3. Should reach dashboard

### Test 5: Menu Upload
1. Upload a menu photo
2. Should get recommendations

### Test 6: Restaurant Search
1. Search "Chipotle Los Angeles"
2. Should find menu and give recommendations

---

## Troubleshooting

### "502 Bad Gateway" on Render
- Check Render logs for Python errors
- Make sure DATABASE_URL is correct
- Wait - free tier sleeps after 15min, takes 30-60s to wake up

### "CORS Error" in browser console
- Make sure FRONTEND_URL is set correctly in Render
- Redeploy backend after changing

### Emails not arriving
- Check spam folder
- Verify BREVO_API_KEY is correct
- Check Brevo dashboard for delivery logs

### "Invalid credentials" but password is correct
- Make sure you verified your email first!
- Try resending verification email

### Database connection errors
- Check DATABASE_URL has `?sslmode=require` at the end
- Verify tables were created in Neon

---

## Free Tier Limitations

| Service | Limitation | Impact |
|---------|------------|--------|
| **Render** | Sleeps after 15min inactive | First request slow (30-60s) |
| **Neon** | 0.5 GB storage | Plenty for MVP |
| **Vercel** | 100 GB bandwidth | Plenty for MVP |
| **Brevo** | 300 emails/day | Plenty for testing |

---

## URLs Reference (fill in after deploying)

```
Frontend:  https://_______________.vercel.app
Backend:   https://_______________.onrender.com
Database:  (in Neon dashboard)
Health:    https://_______________.onrender.com/health
API Docs:  https://_______________.onrender.com/docs
```

---

## You Did It! 🎉

Your app is now live on the internet. Share the Vercel URL with friends!

Next steps (optional):
- Buy a custom domain
- Upgrade Render to paid ($7/mo) for no sleep
- Add more features

---


# 🚀 Deployment Guide

## Stack
| Service | Purpose | URL |
|---------|---------|-----|
| Vercel | Frontend | TBD |
| Render | Backend | TBD |
| Neon | Database | TBD |
| Brevo | Email | ✅ Configured |

## Status
- [x] Local development complete
- [x] Authentication with email verification
- [x] Menu OCR + restaurant search
- [x] AI recommendations
- [ ] Deploy database (Neon)
- [ ] Deploy backend (Render)
- [ ] Deploy frontend (Vercel)

## Environment Variables

### Backend (Render)
```
DATABASE_URL=
JWT_SECRET_KEY=
ANTHROPIC_API_KEY=
BREVO_API_KEY=
GOOGLE_PLACES_API_KEY=
FRONTEND_URL=
```

### Frontend (Vercel)
```
VITE_API_URL= (optional if using rewrites)
```

## Deployment Steps
1. Create Neon database + run schema
2. Deploy backend to Render
3. Deploy frontend to Vercel
4. Update CORS/URLs
5. Test full flow

---

*Deployment in progress - ETA: This weekend*
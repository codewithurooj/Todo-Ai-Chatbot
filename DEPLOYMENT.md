# Deployment Guide

## 🌐 Live URLs

### Backend API
- **Base URL**: https://todo-ai-chatbot.onrender.com
- **Health Check**: https://todo-ai-chatbot.onrender.com/health
- **API Documentation**: https://todo-ai-chatbot.onrender.com/docs
- **OpenAPI Schema**: https://todo-ai-chatbot.onrender.com/openapi.json

### Frontend (Coming Soon)
- **Live App**: TBD (Deploy to Vercel next)

---

## 🚀 Deployment Status

| Service | Platform | Status | URL |
|---------|----------|--------|-----|
| **Backend** | Render | ✅ Live | https://todo-ai-chatbot.onrender.com |
| **Frontend** | Vercel | ⏳ Pending | TBD |
| **Database** | Neon | ✅ Live | PostgreSQL (serverless) |

---

## 📦 Backend Deployment (Render)

### Configuration
- **Platform**: Render
- **Plan**: Free Tier
- **Region**: Oregon (US West)
- **Runtime**: Python 3.13.4
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables
```env
DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech/[db]?sslmode=require
BETTER_AUTH_SECRET=[your-secret-key]
OPENAI_API_KEY=[your-openai-key]
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
OPENAI_MODEL=gpt-4o-mini
```

### Health Check
```bash
curl https://todo-ai-chatbot.onrender.com/health
```

Expected Response:
```json
{
  "status": "healthy",
  "components": {
    "api": "ok",
    "database": "ok",
    "openai": "ok"
  },
  "version": "3.0.0"
}
```

---

## 🗄️ Database (Neon PostgreSQL)

### Configuration
- **Provider**: Neon
- **Type**: Serverless PostgreSQL
- **Region**: US East 1
- **SSL**: Required
- **Tables**: 5 (users, tasks, conversations, messages, alembic_version)

### Connection
Connection string is stored in Render environment variables as `DATABASE_URL`.

### Migrations
Migrations run automatically on deployment via Alembic.

---

## 🔐 Security

### Implemented
- ✅ JWT authentication with Bearer tokens
- ✅ Rate limiting (100/hour, 20/minute per user)
- ✅ Input validation and sanitization
- ✅ CORS protection
- ✅ HTTPS (automatic on Render)
- ✅ Environment variable encryption (Render secrets)
- ✅ SQL injection protection (SQLModel ORM)

### Secrets Management
All sensitive values stored in Render environment variables (encrypted at rest).

---

## 📊 Performance

### Free Tier Limitations
- **Sleep Mode**: Service sleeps after 15 minutes of inactivity
- **Cold Start**: First request after sleep takes 30-60 seconds
- **Monthly Hours**: 750 hours/month
- **Bandwidth**: 100 GB/month

### Optimization Tips
- Use [UptimeRobot](https://uptimerobot.com/) to ping every 14 minutes
- Upgrade to paid tier ($7/month) for 24/7 availability

---

## 🧪 Testing Deployed API

### Test Health Endpoint
```bash
curl https://todo-ai-chatbot.onrender.com/health
```

### Test API Documentation
Visit: https://todo-ai-chatbot.onrender.com/docs

### Test Chat Endpoint (requires auth)
```bash
curl -X POST https://todo-ai-chatbot.onrender.com/api/{user_id}/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {your-jwt-token}" \
  -d '{"message": "Add task to buy groceries"}'
```

---

## 🔄 Continuous Deployment

### Auto-Deploy Enabled
- Pushes to `master` branch trigger automatic redeployment
- Build takes approximately 2-3 minutes
- Zero-downtime deployments

### Manual Deploy
1. Go to Render Dashboard
2. Select `todo-chatbot-api` service
3. Click "Manual Deploy" → "Deploy latest commit"

---

## 🐛 Troubleshooting

### Build Failures
**Problem**: Dependencies fail to install
**Solution**: Check `requirements.txt` has all packages

**Problem**: Python version mismatch
**Solution**: Verify `runtime.txt` specifies `python-3.13.0`

### Runtime Errors
**Problem**: Database connection fails
**Solution**: Verify `DATABASE_URL` is set correctly in Render environment

**Problem**: Import errors (ModuleNotFoundError)
**Solution**: Check package is in `requirements.txt`

### Cold Start Issues
**Problem**: First request times out
**Solution**: Render free tier sleeps after inactivity. Use UptimeRobot or upgrade.

### CORS Errors
**Problem**: Frontend can't connect to API
**Solution**: Add frontend URL to `CORS_ORIGINS` environment variable

---

## 📝 Next Steps

1. ✅ **Backend Deployed** - Complete
2. ⏳ **Deploy Frontend to Vercel** - Next
3. ⏳ **Update CORS Settings** - Add Vercel URL to backend
4. ⏳ **End-to-End Testing** - Test full user flow
5. ⏳ **Performance Monitoring** - Set up UptimeRobot

---

## 📞 Support

**Render Documentation**: https://render.com/docs
**Neon Documentation**: https://neon.tech/docs
**GitHub Repository**: https://github.com/codewithurooj/Todo-Ai-Chatbot

---

**Deployment Date**: December 24, 2025
**Last Updated**: December 24, 2025

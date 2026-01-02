# Doctor+ Backend

Production-ready FastAPI backend for Doctor+ medical AI assistant, powered by Groq's Llama 3.1 405B model.

## Features

- ✅ FastAPI with async support
- ✅ Groq AI integration (Llama 3.1 405B)
- ✅ Medical safety prompts and disclaimers
- ✅ CORS enabled
- ✅ Structured error handling
- ✅ Health check endpoint
- ✅ Docker support
- ✅ Render-ready deployment
- ✅ Build version tracking

## API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "ok", "build": "2026-01-02-render-a", "groq_configured": true}
```

### Version Info
```bash
GET /version
Response: {"build": "2026-01-02-render-a", "service": "doctorplus-backend"}
```

### AI Chat
```bash
POST /doctorplus
Content-Type: application/json

Request:
{
  "mode": "symptoms",  // or "analyses"
  "text": "У меня болит голова и температура 37.5",
  "image_b64": null  // optional base64 image
}

Response:
{
  "answer_md": "AI response in Markdown...",
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 456,
    "total_tokens": 579
  },
  "build": "2026-01-02-render-a"
}
```

## Local Development

### Prerequisites

- Python 3.11+
- Groq API key ([get one here](https://console.groq.com))

### Setup

1. **Clone repository**
```bash
git clone https://github.com/yourusername/doctorplus-backend.git
cd doctorplus-backend
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

4. **Set environment variables**
```bash
export GROQ_API_KEY="gsk_your_api_key_here"
```

Or create `.env` file (don't commit this!):
```
GROQ_API_KEY=gsk_your_api_key_here
```

5. **Run development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Test endpoints**
```bash
# Health check
curl http://localhost:8000/health

# Version
curl http://localhost:8000/version

# AI request
curl -X POST http://localhost:8000/doctorplus \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "symptoms",
    "text": "У меня болит голова"
  }'
```

## Docker

### Build image
```bash
docker build -t doctorplus-backend .
```

### Run container
```bash
docker run -p 8000:8000 \
  -e GROQ_API_KEY="gsk_your_api_key_here" \
  doctorplus-backend
```

### Test
```bash
curl http://localhost:8000/health
```

## Render Deployment

### Method 1: Web Dashboard (Recommended)

1. **Create new Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure service**
   - **Name**: `doctorplus-backend`
   - **Environment**: `Docker`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Docker Command**: (leave empty, uses Dockerfile CMD)
   
3. **Add environment variable**
   - Key: `GROQ_API_KEY`
   - Value: `gsk_your_api_key_here`

4. **Set health check**
   - Path: `/health`
   - Wait for service to be "Live"

5. **Test deployment**
```bash
curl https://doctorplus-backend.onrender.com/health
```

### Method 2: render.yaml (Infrastructure as Code)

Create `render.yaml` in repository root:

```yaml
services:
  - type: web
    name: doctorplus-backend
    env: docker
    plan: free  # or starter/standard
    region: singapore  # or oregon/frankfurt
    healthCheckPath: /health
    envVars:
      - key: GROQ_API_KEY
        sync: false  # Set manually in dashboard for security
```

Then:
```bash
# Commit and push
git add render.yaml
git commit -m "Add Render deployment config"
git push origin main

# In Render dashboard: New -> Blueprint
# Select repository and apply
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | **Yes** | Groq API authentication key | `gsk_abc123...` |
| `PORT` | No | Server port (auto-set by Render) | `8000` |

## Architecture

```
doctorplus-backend/
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI app with all endpoints
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker build instructions
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Error Handling

The API returns structured errors:

- **500** - `AI service not configured` (missing GROQ_API_KEY)
- **504** - `AI service timeout` (Groq request >60s)
- **429** - `AI service rate limit exceeded`
- **502** - `AI service error` (Groq API failure)
- **400** - Invalid request format

## Monitoring

Check service health:
```bash
curl https://your-service.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "build": "2026-01-02-render-a",
  "groq_configured": true
}
```

## Security Notes

- ✅ GROQ_API_KEY is normalized (strips quotes/whitespace)
- ✅ Non-root user in Docker container
- ✅ No secrets in code or version control
- ✅ CORS configured (update `allow_origins` in production)
- ⚠️ TODO: Add rate limiting middleware
- ⚠️ TODO: Add request logging/monitoring
- ⚠️ TODO: Restrict CORS origins to your frontend domain

## Troubleshooting

### "AI service not configured" error
- Check GROQ_API_KEY is set in Render environment variables
- Verify key has no extra quotes or spaces
- Check Render logs: Settings → Logs

### Health check failing
- Wait 40-60 seconds for container startup
- Check Render logs for Python errors
- Verify PORT is being used correctly

### Groq API errors
- Check your API key is valid at console.groq.com
- Verify you haven't hit rate limits
- Check Groq service status

## Production Checklist

Before going live:

- [ ] Set GROQ_API_KEY in Render environment
- [ ] Update CORS `allow_origins` to your frontend domain
- [ ] Enable Render health checks
- [ ] Set up monitoring/alerting
- [ ] Configure custom domain (if needed)
- [ ] Add rate limiting middleware
- [ ] Set up logging aggregation
- [ ] Test all endpoints in production
- [ ] Document API for frontend team

## License

MIT

## Support

For issues and questions:
- GitHub Issues: [Create issue](https://github.com/yourusername/doctorplus-backend/issues)
- Groq API: [Groq Documentation](https://console.groq.com/docs)
- Render: [Render Documentation](https://render.com/docs)

# Doctor+ Backend API

Production-ready FastAPI backend for Doctor+ medical AI assistant (50+ audience optimized).

**Version:** 2026-01-02-render-a  
**AI Model:** Groq Llama 3.1 70B Versatile (configurable with fallback)  
**Deployment:** Docker on Render

## ✨ Features

- ✅ **Versioned API** - `/v1/*` endpoints for stable client integration
- ✅ **Client Authentication** - X-API-Key or Bearer token
- ✅ **Rate Limiting** - 30 requests/minute per IP (configurable)
- ✅ **Safety Filtering** - Blocks unsafe requests with helpful responses
- ✅ **CORS Configuration** - Environment-specific origin control
- ✅ **Standardized Errors** - Consistent JSON error format with codes
- ✅ **Structured Logging** - Request IDs, timing, sanitized logs
- ✅ **50+ Optimized** - Simple language, structured responses
- ✅ **Legacy Support** - Backward-compatible `/doctorplus` endpoint

## 📋 API Endpoints

### Root & Health
```bash
GET /                # Service info and endpoint list
GET /health          # Legacy health check
GET /version         # Legacy version info
GET /v1              # V1 API info
GET /v1/health       # V1 health check  
GET /v1/version      # V1 version info
```

### Main AI Endpoint (V1 - Production)
```bash
POST /v1/doctorplus  # Requires authentication
```

**Request:**
```json
{
  "mode": "symptoms",
  "text": "У меня болит голова и температура 37.5",
  "image_b64": null
}
```

**Headers:**
```
X-API-Key: your_api_key
# OR
Authorization: Bearer your_api_key
```

**Response (200):**
```json
{
  "answer_md": "**1. Что это может быть**\n\n• Простуда или ОРВИ...",
  "usage": {
    "prompt_tokens": 234,
    "completion_tokens": 456,
    "total_tokens": 690
  },
  "build": "2026-01-02-render-a"
}
```

**Response (429 Rate Limit):**
```json
{
  "error": {
    "code": "RATE_LIMIT",
    "message": "Rate limit exceeded: 30 requests per minute",
    "details": {
      "limit": 30,
      "remaining": 0,
      "reset_at": 1704196800
    },
    "build": "2026-01-02-render-a"
  }
}
```

### Legacy Endpoint (Deprecated)
```bash
POST /doctorplus     # Same as /v1/doctorplus, adds Deprecation header
```

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- Groq API key: https://console.groq.com/keys

### Setup

```bash
# Clone and enter directory
git clone https://github.com/aNikikita/doctorplus-backend.git
cd doctorplus-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="gsk_your_groq_api_key"
export DOCTORPLUS_API_KEY="your_client_api_key"  # Optional in dev
export ENVIRONMENT="dev"

# Run server
uvicorn app.main:app --reload --port 8000
```

### Test Locally

```bash
# Health check
curl http://localhost:8000/health

# V1 health
curl http://localhost:8000/v1/health

# AI request (with auth)
curl -X POST http://localhost:8000/v1/doctorplus \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_client_api_key" \
  -d '{"mode":"symptoms","text":"У меня болит голова"}'

# Run smoke tests
chmod +x scripts/smoke_test.sh
./scripts/smoke_test.sh http://localhost:8000
```

## 🐳 Docker

```bash
# Build image
docker build -t doctorplus-backend .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY="gsk_your_key" \
  -e DOCTORPLUS_API_KEY="your_client_key" \
  -e ENVIRONMENT="prod" \
  -e ALLOWED_ORIGINS="https://yourdomain.com" \
  doctorplus-backend

# Test
curl http://localhost:8000/health
```

## ☁️ Render Deployment

### Step 1: Create Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository: `aNikikita/doctorplus-backend`
4. Configure:
   - **Name**: `doctorplus-backend`
   - **Environment**: `Docker`
   - **Region**: Singapore (or closest)
   - **Branch**: `main`

### Step 2: Environment Variables

Add these in Render Dashboard → Environment:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | `gsk_abc123...` | Groq API key (get from console.groq.com) |
| `DOCTORPLUS_API_KEY` | **Yes (prod)** | `dp_prod_xyz789` | Client authentication key (generate secure random) |
| `ENVIRONMENT` | **Yes** | `prod` | Set to `prod` for production |
| `ALLOWED_ORIGINS` | **Yes (prod)** | `https://app.com,https://admin.com` | Comma-separated allowed origins |
| `DOCTORPLUS_RPM` | No | `30` | Rate limit (requests per minute, default 30) |
| `DEBUG_ENDPOINTS` | No | `0` | Enable /debug/env endpoint (0 or 1) |
| `REQUIRE_LEGACY_AUTH` | No | `0` | Require auth for legacy /doctorplus (0 or 1) |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_USER_SNIPPET` | No | `0` | Log first 80 chars of user text (0 or 1) |

### Step 3: Health Check

Set health check path to: `/health`

### Step 4: Deploy

Click **"Create Web Service"** and wait 3-5 minutes.

Your API will be live at: `https://doctorplus-backend-xxx.onrender.com`

### Step 5: Verify Deployment

```bash
# Set your Render URL
export RENDER_URL="https://doctorplus-backend-xxx.onrender.com"

# Health check
curl $RENDER_URL/health

# V1 version
curl $RENDER_URL/v1/version

# Test auth (should return 401)
curl -X POST $RENDER_URL/v1/doctorplus \
  -H "Content-Type: application/json" \
  -d '{"mode":"symptoms","text":"test"}'

# Test with valid key
curl -X POST $RENDER_URL/v1/doctorplus \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_doctorplus_api_key" \
  -d '{"mode":"symptoms","text":"У меня болит голова"}'

# Run smoke tests
./scripts/smoke_test.sh $RENDER_URL
```

## 🔧 Configuration

### Environment Variables Reference

#### Required (Production)

- **`GROQ_API_KEY`** - Groq API authentication key
- **`DOCTORPLUS_API_KEY`** - Client API key for `/v1/*` endpoints
- **`ENVIRONMENT`** - `dev` or `prod` (affects CORS and auth)
- **`ALLOWED_ORIGINS`** - Comma-separated list of allowed CORS origins (required in prod)

#### Optional

- **`GROQ_MODEL`** - Primary Groq model name (default: `llama-3.1-70b-versatile`)
- **`GROQ_FALLBACK_MODEL`** - Fallback Groq model name (default: `llama-3.1-8b-instant`)
- **`DOCTORPLUS_RPM`** - Rate limit (default: 30 requests/minute)
- **`DEBUG_ENDPOINTS`** - Enable `/debug/env` endpoint (default: 0)
- **`REQUIRE_LEGACY_AUTH`** - Require auth for legacy `/doctorplus` (default: 0)
- **`LOG_LEVEL`** - Logging verbosity: DEBUG, INFO, WARNING, ERROR (default: INFO)
- **`LOG_USER_SNIPPET`** - Log first 80 chars of user text (default: 0 for privacy)

### Development vs Production

**Development (`ENVIRONMENT=dev`):**
- CORS: `["*"]` if `ALLOWED_ORIGINS` not set
- Auth: `/v1/*` optional if `DOCTORPLUS_API_KEY` not set
- Logging: More verbose

**Production (`ENVIRONMENT=prod`):**
- CORS: Explicit `ALLOWED_ORIGINS` required (no wildcard)
- Auth: `DOCTORPLUS_API_KEY` required
- Validation: Strict startup checks

## 🔐 Security

### Authentication

All `/v1/*` endpoints (except `/v1/health` and `/v1/version`) require authentication:

```bash
# Option 1: X-API-Key header
curl -H "X-API-Key: your_key" ...

# Option 2: Bearer token
curl -H "Authorization: Bearer your_key" ...
```

### Generate Secure API Key

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Rate Limiting

- **Limit**: 30 requests/minute per IP (configurable via `DOCTORPLUS_RPM`)
- **Headers**: Response includes `X-RateLimit-*` headers
- **429 Error**: Returns reset timestamp and remaining quota

### Safety Filtering

Unsafe requests (self-harm, violence, etc.) are blocked with:
- HTTP 400
- Error code: `UNSAFE_REQUEST`
- Supportive message with emergency contacts (051, 112, 8-800-2000-122)

## 📖 Frontend Integration

**⚠️ ВАЖНО**: Web и Flutter приложения должны обращаться к `{RENDER_URL}/v1/doctorplus`, **НЕ** к `/api/*`

Этот backend **НЕ использует** префикс `/api`. Все маршруты начинаются с корня:
- ✅ `https://your-backend.onrender.com/v1/doctorplus`
- ❌ `https://your-backend.onrender.com/api/doctorplus` (вернёт 404)

### Next.js (web_v2)

```typescript
// lib/config.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://doctorplus-backend-xxx.onrender.com';
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

// lib/api/doctorplus.ts
export async function sendDoctorPlusRequest(
  mode: 'symptoms' | 'analyses',
  text: string
) {
  const response = await fetch(`${API_BASE_URL}/v1/doctorplus`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY!
    },
    body: JSON.stringify({ mode, text })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'API error');
  }
  
  return await response.json();
}
```

### Flutter (mobile)

```dart
// lib/config/api_config.dart
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://doctorplus-backend-xxx.onrender.com',
  );
  static const String apiKey = String.fromEnvironment('API_KEY');
}

// lib/services/doctorplus_api.dart
Future<DoctorPlusResponse> sendRequest(String mode, String text) async {
  final response = await dio.post(
    '${ApiConfig.baseUrl}/v1/doctorplus',
    data: {'mode': mode, 'text': text},
    options: Options(headers: {
      'X-API-Key': ApiConfig.apiKey,
    }),
  );
  return DoctorPlusResponse.fromJson(response.data);
}
```

## 🐛 Error Codes

All errors return standardized JSON:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... },
    "build": "2026-01-02-render-a"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `NOT_FOUND` | 404 | Endpoint not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMIT` | 429 | Too many requests |
| `UNSAFE_REQUEST` | 400 | Unsafe content detected |
| `AI_NOT_CONFIGURED` | 500 | GROQ_API_KEY not set |
| `AI_TIMEOUT` | 504 | AI request timeout (>60s) |
| `AI_RATE_LIMIT` | 429 | Groq API rate limit |
| `AI_AUTH_FAILED` | 502 | Groq API authentication failed |
| `AI_UPSTREAM_ERROR` | 502 | Groq API error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## 📊 Monitoring

### Health Checks

```bash
# Basic health
curl https://your-service.onrender.com/health

# V1 health with version
curl https://your-service.onrender.com/v1/version
```

### Logs (Render Dashboard)

Navigate to: Dashboard → Your Service → Logs

Look for:
- `🚀 Doctor+ Backend starting` - Startup info
- `[request_id]` - Request tracking
- `latency=XXXms` - Response timing
- `Groq success: tokens=XXX` - AI completions

### Debug Endpoint (if enabled)

```bash
# Set DEBUG_ENDPOINTS=1 in environment
curl https://your-service.onrender.com/debug/env
```

## 🧪 Testing

### Run Smoke Tests

```bash
# Local
./scripts/smoke_test.sh http://localhost:8000

# Production (set DOCTORPLUS_API_KEY env var first)
export DOCTORPLUS_API_KEY="your_production_key"
./scripts/smoke_test.sh https://doctorplus-backend-xxx.onrender.com
```

Tests verify:
- ✓ All endpoints return expected status codes
- ✓ Authentication works
- ✓ Rate limiting headers present
- ✓ Error format consistent

## 🚨 Troubleshooting

### "GROQ_API_KEY is required" on startup

**Cause**: Missing or empty `GROQ_API_KEY`  
**Fix**: Set environment variable in Render dashboard

### "DOCTORPLUS_API_KEY is required in production"

**Cause**: `ENVIRONMENT=prod` but no `DOCTORPLUS_API_KEY` set  
**Fix**: Generate secure key and add to environment variables

### "ALLOWED_ORIGINS must be explicitly set in production"

**Cause**: `ENVIRONMENT=prod` but no `ALLOWED_ORIGINS` set  
**Fix**: Set comma-separated list of allowed domains

### 401 UNAUTHORIZED on /v1/doctorplus

**Cause**: Missing or invalid API key  
**Fix**: Include `X-API-Key` or `Authorization: Bearer` header

### 429 RATE_LIMIT

**Cause**: Exceeded 30 requests/minute  
**Fix**: Wait until `X-RateLimit-Reset` timestamp or increase `DOCTORPLUS_RPM`

### 504 AI_TIMEOUT

**Cause**: Groq API took >60 seconds  
**Fix**: Retry request; check Groq service status

## 📦 Project Structure

```
doctorplus-backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with all endpoints
│   ├── config.py        # Environment configuration
│   ├── security.py      # Authentication & IP extraction
│   ├── rate_limit.py    # In-memory rate limiter
│   └── errors.py        # Standardized error handling
├── scripts/
│   └── smoke_test.sh    # Automated endpoint testing
├── Dockerfile           # Docker build instructions
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 📄 License

MIT

## 🤝 Support

- **GitHub**: https://github.com/aNikikita/doctorplus-backend/issues
- **Groq Console**: https://console.groq.com
- **Render Docs**: https://render.com/docs

---

**Built with** ❤️ **for 50+ health awareness**

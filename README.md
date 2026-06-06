# Qwen Chat App

A production-ready web application for chatting with Qwen AI model via Ollama. React frontend + FastAPI backend, fully containerized and ready for deployment to Emergent Labs.

## Architecture

```
Frontend (React + TypeScript)  →  Backend (FastAPI)  →  Ollama (Local or Remote)
         :5173                         :8000                   :11434
```

## Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Ollama running locally (or accessible remotely)

### Option 1: Docker Compose (Recommended)

```bash
cd qwen-chat-app
docker-compose up
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Ollama: http://localhost:11434 (if using Docker container)

### Option 2: Local Development

**Terminal 1 - Backend:**
```bash
cd qwen-chat-app/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd qwen-chat-app
npm install
npm run dev
```

## Environment Variables

### Backend (`.env`)
```
OLLAMA_BASE_URL=http://localhost:11434    # Ollama server URL
MODEL_NAME=qwen2.5:0.5b                  # Model to use
```

> The backend also supports `OLLAMA_HOST` for compatibility.

### Frontend (`.env.local`)
```
VITE_API_URL=http://localhost:8000       # Backend API URL for local development
```

> In production, the frontend is served by Nginx and uses a relative `/api` path by default.

## Build for Production

### Build Frontend
```bash
npm run build
# Output: ./dist/
```

### Build Docker Image
```bash
docker build -t supportcaretraining/qwen-chat-app:latest .
docker push supportcaretraining/qwen-chat-app:latest
```

## Deployment to Emergent Labs

### Step 1: Prepare Code Repository

```bash
# Ensure all files are committed
git init
git add .
git commit -m "Initial commit: Qwen Chat App"
```

### Step 2: Create Emergent Labs Configuration

Create `emergent.yml` in root directory if Emergent Labs requires an app manifest:

```yaml
version: 1
name: qwen-chat-app
description: "Qwen Chat Application with FastAPI backend"

services:
  api:
    image: supportcaretraining/qwen-chat-app:latest
    port: 8000
    environment:
      - OLLAMA_HOST=${OLLAMA_HOST}
      - MODEL_NAME=${MODEL_NAME}
    healthcheck:
      path: /api/health
      interval: 30s

  frontend:
    serves: ./dist
    port: 3000

resources:
  compute: "2GB"
  memory: "1GB"
```

### Step 3: Deploy

```bash
# Push to Emergent Labs
emergent deploy --config emergent.yml

# Or via web console
# 1. Go to app.emergent.ai
# 2. Click "New App"
# 3. Connect GitHub repo
# 4. Set environment variables
# 5. Deploy
```

### Step 4: Configure Environment (in Emergent Console)

```
OLLAMA_HOST = https://your-ollama-endpoint.com
MODEL_NAME = qwen2.5:0.5b
```

## API Endpoints

### Health Check
```bash
GET /api/health
```
Response:
```json
{
  "status": "ok",
  "ollama": "connected",
  "models": 1
}
```

### Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ]
}
```

Response:
```json
{
  "response": "I'm doing well, thank you for asking!",
  "model": "qwen2.5:0.5b"
}
```

## Project Structure

```
qwen-chat-app/
├── src/
│   ├── App.tsx          # Main React component
│   ├── App.css          # Styling
│   └── main.tsx         # Entry point
├── backend/
│   ├── main.py          # FastAPI application
│   └── requirements.txt  # Python dependencies
├── public/              # Static assets
├── Dockerfile           # Production image
├── docker-compose.yml   # Local development
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript config
├── package.json         # Frontend dependencies
└── README.md            # This file
```

## Features

✅ Real-time chat interface  
✅ Message history support  
✅ Connection status monitoring  
✅ Mobile-responsive design  
✅ Docker containerization  
✅ FastAPI backend with async support  
✅ CORS enabled for cross-origin requests  
✅ Health check endpoint  
✅ Production-ready Dockerfile  

## Troubleshooting

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Check OLLAMA_HOST environment variable
- Verify network connectivity

### Frontend can't reach Backend
- Check backend is running on port 8000
- Verify VITE_API_URL in frontend env
- Check CORS configuration in backend

### Model not found
- Pull the model: `ollama pull qwen2.5:0.5b`
- Verify model name in MODEL_NAME env variable

## Performance Tips

1. **Use smaller models for faster responses:** `qwen2.5:0.5b` (default)
2. **Increase context length cautiously** (impacts memory usage)
3. **Enable request caching** in production
4. **Use CDN for static assets** (Emergent Labs handles this)

## License

MIT

## Support

For issues or questions:
- Check backend logs: `docker logs qwen-chat-backend`
- Check frontend console: Browser DevTools
- Verify Ollama: `curl http://localhost:11434/api/tags`

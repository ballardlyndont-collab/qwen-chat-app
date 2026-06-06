## 🚀 Deploy to Emergent Labs

Your Qwen Chat App is ready to deploy to Emergent Labs with your 150 credits.

### Prerequisites
- Emergent Labs account (app.emergent.ai)
- This code repository
- Docker Hub account (optional but recommended)

---

## Step 1: Prepare Docker Image

### Option A: Push to Docker Hub
```bash
docker login
docker build -t yourusername/qwen-chat-app:latest .
docker push yourusername/qwen-chat-app:latest
```

### Option B: Use Emergent's Registry
Emergent Labs provides a private registry. Check their docs for the registry URL and credentials.

---

## Step 2: Configure Deployment

Create `emergent-deploy.yml` in your repo root:

```yaml
name: qwen-chat-app
version: 1.0.0
description: Qwen Chat with local Ollama integration

services:
  web:
    image: yourusername/qwen-chat-app:latest
    port: 8000
    environment:
      - OLLAMA_HOST=${OLLAMA_HOST}
      - MODEL_NAME=${MODEL_NAME}
    resources:
      memory: 2Gi
      cpu: 1000m
    healthcheck:
      path: /api/health
      interval: 30s
      timeout: 10s
      retries: 3

autoscale:
  min: 1
  max: 3
  target_cpu: 70%

environment:
  OLLAMA_HOST: http://localhost:11434
  MODEL_NAME: qwen2.5:0.5b
```

---

## Step 3: Deploy via Web Console

1. **Login to app.emergent.ai**
2. **Create New App** → Select "Docker Container"
3. **Image Source:**
   - Choose "Docker Hub" or "Emergent Registry"
   - Image: `yourusername/qwen-chat-app:latest`
4. **Configuration:**
   - Name: `qwen-chat-app`
   - Port: `8000`
5. **Environment Variables:**
   ```
   OLLAMA_HOST = http://localhost:11434
   MODEL_NAME = qwen2.5:0.5b
   ```
6. **Resources:**
   - Memory: 2 GB
   - CPU: 1 vCPU
   - Estimated cost: ~15-20 credits/month
7. **Click Deploy**

---

## Step 4: Configure Ollama Access

### Option A: Local Ollama
If Ollama runs on the same machine:
```
OLLAMA_HOST = http://localhost:11434
```

### Option B: Remote Ollama (Recommended for Production)
Set up Ollama on a separate machine/server:
```
OLLAMA_HOST = https://ollama.your-domain.com
```

Alternatively, Emergent Labs can run Ollama in a separate container:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    port: 11434
    volumes:
      - ollama_data:/root/.ollama
    resources:
      memory: 4Gi
      gpu: true  # If available in Emergent Labs
```

---

## Step 5: Verify Deployment

Once deployed:

```bash
# Check health
curl https://your-app.emergent.app/api/health

# Test chat endpoint
curl -X POST https://your-app.emergent.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "history": []}'
```

---

## Step 6: Access Your App

**Frontend:** `https://your-app.emergent.app`  
**API Docs:** `https://your-app.emergent.app/docs`  
**API:** `https://your-app.emergent.app/api`

---

## Cost Breakdown (150 Credits)

| Service | Cost/Month | Duration |
|---------|-----------|----------|
| Web App (2GB RAM, 1 vCPU) | 15-20 credits | 7-10 months |
| Optional: Ollama (4GB RAM, GPU) | 30-40 credits | 3-5 months |

**Recommendation:** Use community Ollama endpoint or local Ollama to extend your 150 credits.

---

## Continuous Deployment (Optional)

Connect GitHub for auto-deploy on push:

1. Go to **Settings** → **Deployment**
2. **GitHub Integration** → Authorize
3. Select repository branch
4. Choose auto-deploy on push

Now every `git push` triggers a new deployment!

---

## Troubleshooting

### App won't start
```bash
# Check logs in Emergent Labs dashboard
# Or via CLI:
emergent logs qwen-chat-app
```

### Ollama unreachable
- Verify `OLLAMA_HOST` is correct and accessible
- Check firewall rules
- Test with: `curl $OLLAMA_HOST/api/tags`

### High memory usage
- Reduce model size: Use `qwen2.5:0.5b` (already optimized)
- Limit concurrent requests in FastAPI
- Scale down instance size if possible

### Slow responses
- Increase CPU allocation
- Use GPU if available
- Pre-load model in Ollama

---

## Next Steps

✅ App deployed  
📊 Monitor performance in Emergent Labs dashboard  
📈 Set up alerts for errors  
🔄 Enable auto-scaling as traffic grows  
🔐 Configure authentication/API keys for production  
📱 Share your app URL with users  

---

**Your app is live!** 🎉

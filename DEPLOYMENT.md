# 🚀 Deployment Guide - FREE Hosting

This guide will help you deploy your biomedical GraphRAG application completely **FREE**.

## 📊 Cost Breakdown (Monthly)

| Service | Cost | What You Get |
|---------|------|--------------|
| **Vercel** (Frontend) | $0 | Unlimited Next.js deployments |
| **Render** (Backend) | $0 | 750 hours (sleeps after 15min idle) |
| **Neo4j Aura** | $0 | 50k nodes, 175k relationships |
| **Qdrant Cloud** | $0 | 1GB vector storage |
| **Prefect Cloud** | $0 | 20k task runs/month |
| **Groq** (AI) | $0 | 14,400 requests/day |
| **TOTAL** | **$0/month** | 🎉 Perfect for portfolio! |

---

## 🎯 Step-by-Step Deployment

### Prerequisites ✅
- [x] Neo4j Aura account (free tier)
- [x] Qdrant Cloud account (free tier)  
- [x] Prefect Cloud account (free tier)
- [ ] Groq API account (sign up below)
- [ ] Vercel account
- [ ] Render account
- [ ] GitHub repository

---

## 1️⃣ Setup Groq (FREE AI Model)

### Why Groq?
- ✅ **FREE**: 14,400 requests/day
- ✅ **Fast**: Up to 500 tokens/sec
- ✅ **OpenAI-compatible API**
- ✅ Models: Llama 3.1 70B, Mixtral, Gemma

### Get API Key:
```bash
# 1. Go to https://console.groq.com
# 2. Sign up (free)
# 3. Create API key
# 4. Copy your key
```

### Alternative Options:
**OpenRouter** ($25 free credits): https://openrouter.ai
- Llama 3.1 70B: $0.35/1M tokens (70x cheaper than GPT-4)
- Access to 100+ models

**Together AI** ($25 free credits): https://api.together.xyz
- Llama 3.1 70B: $0.88/1M tokens

---

## 2️⃣ Deploy Backend (Render)

### A. Push to GitHub
```bash
git add render.yaml requirements.txt
git commit -m "feat: Add deployment configs"
git push origin main
```

### B. Deploy on Render
1. Go to https://render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select `render.yaml`
5. Click **"Apply"**

### C. Set Environment Variables
In Render dashboard, add these environment variables:

**Neo4j (from Neo4j Aura):**
```bash
NEO4J__URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=your_password
```

**Qdrant (from Qdrant Cloud):**
```bash
QDRANT__URL=https://xxxxx.cloud.qdrant.io:6333
QDRANT__API_KEY=your_api_key
```

**Groq (from console.groq.com):**
```bash
OPENAI__API_KEY=gsk_xxxxx
# Already set in render.yaml:
# OPENAI__BASE_URL=https://api.groq.com/openai/v1
# OPENAI__MODEL=llama-3.1-70b-versatile
```

**Prefect Cloud (optional):**
```bash
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/xxx/workspaces/xxx
PREFECT_API_KEY=pnu_xxxxx
```

### D. Deploy
Click **"Create Web Service"** - Render will automatically deploy!

Your API will be at: `https://biomedical-graphrag-api.onrender.com`

---

## 3️⃣ Deploy Frontend (Vercel)

### A. Install Vercel CLI
```bash
npm install -g vercel
vercel login
```

### B. Configure Environment
Create `frontend/.env.production`:
```bash
NEXT_PUBLIC_API_URL=https://biomedical-graphrag-api.onrender.com
```

### C. Deploy
```bash
cd frontend
vercel --prod
```

Or connect via GitHub:
1. Go to https://vercel.com
2. Click **"New Project"**
3. Import your GitHub repository
4. Set **Root Directory**: `frontend`
5. Add environment variable: `NEXT_PUBLIC_API_URL`
6. Click **"Deploy"**

Your frontend will be at: `https://biomedical-graphrag.vercel.app`

---

## 4️⃣ Setup Databases (If Not Done)

### Neo4j Aura (FREE)
```bash
# 1. Go to https://neo4j.com/cloud/aura-free/
# 2. Create free instance
# 3. Download credentials
# 4. Note connection URI
```

### Qdrant Cloud (FREE)
```bash
# 1. Go to https://cloud.qdrant.io
# 2. Create free cluster
# 3. Create API key
# 4. Note cluster URL
```

### Prefect Cloud (FREE)
```bash
# 1. Go to https://app.prefect.cloud
# 2. Create workspace
# 3. Generate API key
# 4. Note API URL
```

---

## 5️⃣ Initial Data Load

### Load Your Data
```bash
# Set environment variables locally
export NEO4J__URI="neo4j+s://xxxxx.databases.neo4j.io"
export NEO4J__USERNAME="neo4j"
export NEO4J__PASSWORD="your_password"
export QDRANT__URL="https://xxxxx.cloud.qdrant.io:6333"
export QDRANT__API_KEY="your_api_key"
export OPENAI__API_KEY="gsk_xxxxx"  # Groq key
export OPENAI__BASE_URL="https://api.groq.com/openai/v1"

# Create graph and vector store
make create-graph
make create-qdrant-collection
make ingest-qdrant-data
```

---

## 🔍 Testing Your Deployment

### 1. Test Backend API
```bash
curl https://biomedical-graphrag-api.onrender.com/api/health/
```

### 2. Test Frontend
Visit: `https://biomedical-graphrag.vercel.app`

### 3. Test Query
```bash
curl -X POST https://biomedical-graphrag-api.onrender.com/api/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the latest findings on CRISPR?", "mode": "hybrid", "limit": 5}'
```

---

## 📈 Monitoring & Optimization

### Render (Backend)
- **Free tier sleeps after 15min idle**
- First request after sleep: ~30s cold start
- Keep-alive: Use a cron job to ping every 14 minutes

### Vercel (Frontend)
- No sleep, instant responses
- Automatic CDN caching
- Monitor usage in dashboard

### Rate Limits
- **Groq**: 14,400 requests/day (600/hour)
- **Render**: 750 hours/month
- **Neo4j Aura**: 50k nodes
- **Qdrant Cloud**: 1GB storage

---

## 🎨 Custom Domain (Optional)

### Vercel (Frontend)
1. Go to Vercel dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records

### Render (Backend)
1. Go to Render dashboard → Settings
2. Add custom domain
3. Update DNS records

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs on Render dashboard
# Common issues:
# - Missing environment variables
# - Incorrect database URLs
# - Python version mismatch
```

### Frontend can't connect to backend
```bash
# Check NEXT_PUBLIC_API_URL in Vercel
# Ensure it includes https://
# Test backend health endpoint first
```

### Database connection issues
```bash
# Neo4j: Check URI format (neo4j+s://)
# Qdrant: Check URL includes port :6333
# Test connections locally first
```

---

## 💡 Cost Optimization Tips

1. **Use Groq's free tier** (14,400 req/day) before paying for OpenAI
2. **Render sleeps after 15min** - expect cold starts (30s)
3. **Monitor Neo4j node count** - stay under 50k for free tier
4. **Qdrant storage** - 1GB should handle ~1M vectors
5. **Prefect Cloud** - 20k task runs/month is generous

---

## 🚀 Upgrade Path (When Needed)

| Service | Free → Paid | Cost | When to Upgrade |
|---------|-------------|------|-----------------|
| **Render** | Hobby Plan | $7/mo | No cold starts needed |
| **Neo4j** | Professional | $65/mo | >50k nodes |
| **Qdrant** | Cloud | $25/mo | >1GB storage |
| **Groq** | Pay-as-go | $0.27/1M | >14k requests/day |

---

## ✅ Final Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Vercel  
- [ ] Neo4j Aura connected
- [ ] Qdrant Cloud connected
- [ ] Groq API working
- [ ] Data loaded
- [ ] Health check passes
- [ ] Test query works
- [ ] Added to portfolio/resume

---

## 📚 Resources

- **Groq Docs**: https://console.groq.com/docs
- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Neo4j Aura**: https://neo4j.com/docs/aura
- **Qdrant Cloud**: https://qdrant.tech/documentation/cloud
- **Prefect Cloud**: https://docs.prefect.io/cloud

---

**Need help?** Open an issue on GitHub or check the troubleshooting section above.

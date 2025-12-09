# Railway Deployment Guide

This guide will help you deploy the BioMedical GraphRAG API to Railway.

## Prerequisites

- Railway account (free tier works!)
- OpenAI API key
- Neo4j Aura database (already set up)
- Qdrant Cloud cluster (already set up)

## Step 1: Install Railway CLI (Optional)

```bash
npm install -g @railway/cli
railway login
```

## Step 2: Deploy via GitHub (Recommended)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository: `paul-data-ai/biomedical_graphrag`
4. Click "Deploy Now"

Railway will automatically detect your Python app and deploy it!

## Step 3: Configure Environment Variables

Once deployed, go to your project settings and add these environment variables:

### Required Variables:

```
OPENAI__API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
OPENAI__MODEL=gpt-4o-mini
OPENAI__TEMPERATURE=0.0
OPENAI__MAX_TOKENS=1500

NEO4J__URI=YOUR_NEO4J_AURA_URI
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=YOUR_NEO4J_PASSWORD
NEO4J__DATABASE=neo4j

QDRANT__URL=YOUR_QDRANT_CLOUD_URL
QDRANT__API_KEY=YOUR_QDRANT_API_KEY
QDRANT__COLLECTION_NAME=biomedical_papers
QDRANT__EMBEDDING_MODEL=text-embedding-3-small
QDRANT__EMBEDDING_DIMENSION=1536
```

**Important:** Use double underscores (`__`) in variable names!

## Step 4: Get Your Railway URL

After deployment:
1. Go to your project in Railway
2. Click on "Settings" → "Domains"
3. Your app will be at: `https://your-app.up.railway.app`

## Step 5: Update Frontend

Update your Vercel frontend environment variable:

```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

Then redeploy your frontend on Vercel.

## Step 6: Update CORS

The Railway URL will be automatically allowed in CORS since we use wildcard origins for production deployments.

## Step 7: Test Your Deployment

```bash
# Health check
curl https://your-app.up.railway.app/api/health/

# OpenAI test
curl https://your-app.up.railway.app/api/health/openai-test

# Stats
curl https://your-app.up.railway.app/api/stats/
```

## Free Tier Limits

Railway free tier includes:
- $5 of usage per month
- 500 hours of execution time
- Unlimited projects
- **Allows external API calls (including OpenAI!)**

This should be sufficient for demo/development purposes!

## Troubleshooting

### Build Fails

If the build fails, Railway might not detect Python correctly. Add a `runtime.txt`:

```
python-3.11
```

### Port Issues

Railway automatically sets the `PORT` environment variable. Our Procfile uses this automatically.

### Logs

View logs in Railway dashboard:
1. Go to your project
2. Click on the service
3. Click "View Logs"

## Automatic Deployments

Railway automatically redeploys when you push to GitHub! No manual steps needed.

## Monitoring

- **Logs:** Available in Railway dashboard
- **Metrics:** CPU, Memory, Network usage shown in dashboard
- **UptimeRobot:** Keep using your existing monitor, just update the URL

## Cost Optimization

To stay within free tier:
- API sleeps after 15 min of inactivity (automatically wakes on request)
- Use UptimeRobot to keep it alive during important times
- Monitor usage in Railway dashboard

## Support

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/paul-data-ai/biomedical_graphrag/issues

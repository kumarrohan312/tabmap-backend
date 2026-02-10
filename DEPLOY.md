# Deploy TABMAP Backend to Render

## Quick Deploy (5 minutes)

### Step 1: Push Code to GitHub

```powershell
cd d:\BMAD\app\backend

# Initialize git (if not already)
git init

# Add all files
git add .
git commit -m "Initial backend commit for Render deployment"

# Create GitHub repo and push
# Go to github.com → New Repository → "tabmap-backend"
git remote add origin https://github.com/YOUR_USERNAME/tabmap-backend.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select **"tabmap-backend"** repository
5. Render will auto-detect settings from `render.yaml`

**Or Manual Setup:**
- **Name:** `tabmap-api`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Set Environment Variables

In Render Dashboard → Environment:

```
MAPBOX_ACCESS_TOKEN = pk.eyJ1Ijoia3VtYXJyb2hhbjMxMiIsImEiOiJjbWxkaDgyOW4xOGp6M2RxNndkbWt6bjE0In0._yZAhf3nY-yLeNvVRtRA_g

CORS_ORIGINS = ["https://web-demo-mu-ten.vercel.app", "https://tabmap.vercel.app", "*"]

ENVIRONMENT = production

REDIS_URL = redis://localhost:6379
```

⚠️ **Important:** Use wildcard `"*"` for CORS during testing, then restrict to your domain later.

### Step 4: Deploy!

- Click **"Create Web Service"**
- Wait 2-3 minutes for build
- Get your API URL: `https://tabmap-api.onrender.com`

### Step 5: Update Frontend

Update `web-demo/index.html` line ~1142:

```javascript
// Change from:
const response = await fetch('http://localhost:8000/routes/optimize', {

// To:
const response = await fetch('https://YOUR-API-NAME.onrender.com/routes/optimize', {
```

Then redeploy frontend:
```powershell
cd d:\BMAD\app\web-demo
vercel --prod
```

---

## Testing

1. Visit: `https://YOUR-API-NAME.onrender.com/health`
2. Should see: `{"status": "healthy"}`
3. Open TABMAP app: `https://web-demo-mu-ten.vercel.app`
4. Test route search - should work!

---

## Free Tier Limits

- ✅ 750 hours/month (always-on with paid plan, spins down after 15 min idle on free)
- ⚠️ First request after idle takes 30-60 seconds (cold start)
- ✅ Unlimited API calls

**To keep always-on:** Upgrade to paid ($7/month) or use cron-job.org to ping `/health` every 10 minutes.

---

## Troubleshooting

**CORS errors:**
- Add `"*"` to CORS_ORIGINS in Render environment variables
- Redeploy service

**Cold starts:**
- Free tier spins down after 15 min idle
- First request will be slow (~30-60s)
- Use UptimeRobot or cron-job.org to keep warm

**Build fails:**
- Check Python version (3.12 required for some deps)
- Verify requirements.txt is in root

---

## Alternative: Railway (Easier, but paid after trial)

If Render is complex, try Railway.app:
1. Visit railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub"
4. Railway auto-detects FastAPI
5. Add same environment variables
6. Deploy!

Railway is simpler but requires credit card after $5 free trial.

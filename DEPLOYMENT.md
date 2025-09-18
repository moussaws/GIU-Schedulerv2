# 🚀 Production Deployment Guide

## Free Hosting on Render.com (100% Free)

This guide will deploy your GIU Staff Schedule Composer to production at **$0/month**.

### Prerequisites
- GitHub account
- Render.com account (free)

### Final Result
- **Backend API**: `https://your-api-name.onrender.com`
- **Frontend**: `https://your-frontend-name.onrender.com`
- **Total Cost**: $0/month forever
- **Custom Domain**: Optional (free subdomain included)

---

## 📋 Step 1: Prepare Your Repository

### 1.1 Initialize Git Repository (if not done)
```bash
cd /Users/moussa/Documents/claude-giu
git init
git add .
git commit -m "Initial deployment setup"
```

### 1.2 Push to GitHub
```bash
# Create repository on GitHub first, then:
git remote add origin https://github.com/yourusername/giu-staff-scheduler.git
git push -u origin main
```

---

## 🔧 Step 2: Deploy Backend API

### 2.1 Create Web Service on Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `giu-scheduler-api`
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you
   - **Branch**: `main`

### 2.2 Environment Variables
Add these environment variables in Render dashboard:

```
DATABASE_URL=sqlite:///./production.db
CORS_ORIGINS=https://your-frontend-name.onrender.com
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False
```

### 2.3 Deploy Backend
- Click **"Create Web Service"**
- Wait for deployment (5-10 minutes)
- Your API will be available at: `https://giu-scheduler-api.onrender.com`

---

## 🎨 Step 3: Deploy Frontend

### 3.1 Create Static Site on Render
1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `giu-scheduler-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Branch**: `main`

### 3.2 Environment Variables for Frontend
Add this environment variable:

```
REACT_APP_API_URL=https://giu-scheduler-api.onrender.com
```

### 3.3 Deploy Frontend
- Click **"Create Static Site"**
- Wait for deployment (5-10 minutes)
- Your app will be available at: `https://giu-scheduler-frontend.onrender.com`

---

## ✅ Step 4: Verify Deployment

### 4.1 Test Backend API
Visit: `https://giu-scheduler-api.onrender.com`
- Should show the API welcome page
- Check: `https://giu-scheduler-api.onrender.com/health`
- API docs: `https://giu-scheduler-api.onrender.com/docs`

### 4.2 Test Frontend
Visit: `https://giu-scheduler-frontend.onrender.com`
- Should load the React application
- Login should work
- All features should be functional

---

## 🔄 Step 5: Auto-Deployment Setup

### 5.1 Enable Auto-Deploy
Both services are automatically configured to redeploy when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main
# Render will automatically rebuild and deploy
```

### 5.2 Deployment Status
- Monitor deployments in Render dashboard
- Check logs for any issues
- Both services have health checks enabled

---

## 🌐 Step 6: Custom Domain (Optional)

### 6.1 Free Subdomain
- Render provides free `.onrender.com` subdomains
- No additional setup required

### 6.2 Custom Domain
If you have your own domain:
1. Go to service settings in Render
2. Add custom domain
3. Update DNS records as instructed
4. SSL certificates are automatically provided

---

## 📊 Free Tier Limits

### Render.com Free Tier:
- **Backend**: 750 hours/month (enough for most usage)
- **Frontend**: Unlimited static hosting
- **SSL**: Included
- **Custom domains**: Supported
- **Automatic scaling**: Included

### Important Notes:
- Backend sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- SQLite database persists between deployments
- No credit card required for free tier

---

## 🛠️ Troubleshooting

### Common Issues:

1. **Build Fails**
   - Check logs in Render dashboard
   - Verify all dependencies are in requirements.txt/package.json

2. **CORS Errors**
   - Ensure CORS_ORIGINS environment variable includes your frontend URL
   - Check both development and production URLs

3. **Database Issues**
   - SQLite database is automatically created on first run
   - Database persists in `/app/data/` directory

4. **Slow First Load**
   - Free tier services sleep after inactivity
   - Use a service like UptimeRobot for keep-alive pings (optional)

---

## 🎯 Production Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Environment variables configured
- [ ] CORS settings working
- [ ] Database initializing properly
- [ ] All API endpoints working
- [ ] Authentication working
- [ ] Frontend connecting to backend
- [ ] Schedule generation working
- [ ] Export functions working

---

## 🔧 Maintenance

### Regular Updates:
```bash
git add .
git commit -m "Feature update"
git push origin main
```

### Monitor:
- Check Render dashboard for service health
- Monitor logs for any errors
- Database grows automatically as needed

### Backup:
- Database is automatically persisted
- Code is backed up in GitHub
- Consider periodic data exports for important schedules

---

**🎉 Congratulations! Your GIU Staff Schedule Composer is now live in production at $0/month!**
# EliWorks Deployment Guide for Render.com

## Prerequisites
1. A Render.com account
2. Your GitHub repository with the latest code
3. A Google Gemini API key

## Deployment Steps

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub (already done)
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository: `ritwikagrawal1228/political-feedback`
5. Render will automatically detect the `render.yaml` file
6. Configure environment variables (see below)
7. Click "Apply"

### Option 2: Manual Setup
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository: `ritwikagrawal1228/political-feedback`
4. Configure the following:
   - **Name**: `eliworks-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application`

## Environment Variables Configuration

In the Render dashboard, add these environment variables:

| Variable Name | Value | Notes |
|---------------|-------|-------|
| `GEMINI_API_KEY` | `your_actual_api_key` | ⚠️ **REQUIRED** - Get from Google AI Studio |
| `GEMINI_MODEL_NAME` | `gemini-pro` | Default model name |
| `FLASK_ENV` | `production` | Production environment |
| `DEBUG_MODE` | `false` | Disable debug mode |
| `PYTHON_VERSION` | `3.11.5` | Python version |

## Important Notes

### 1. Database
- The app uses SQLite which will work on Render's free tier
- Database will be recreated on each deployment (data won't persist)
- For persistent data, consider upgrading to PostgreSQL

### 2. Static Files
- The `/static` folder contains CSS, JS, and uploaded reports
- Reports saved on free tier will be lost on redeploy

### 3. API Key Security
- Never commit your actual API key to GitHub
- Always set `GEMINI_API_KEY` in Render's environment variables
- Use the provided `env.example` as a template

### 4. File Structure
```
├── wsgi.py              # WSGI entry point
├── app.py               # Main Flask application
├── campaigns.py         # Campaign blueprint
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
└── DEPLOYMENT.md        # This file
```

## Testing Deployment

After deployment:
1. Visit your Render URL (e.g., `https://eliworks-app.onrender.com`)
2. You should be redirected to `/campaigns` (dashboard)
3. Test creating a new campaign
4. Test the chat functionality
5. Test report generation (requires valid API key)

## Troubleshooting

### Common Issues:
1. **App won't start**: Check environment variables, especially `GEMINI_API_KEY`
2. **500 Error**: Check Render logs for Python errors
3. **API errors**: Verify your Gemini API key is valid and has credits
4. **Static files missing**: Ensure `/static` folder is committed to git

### Checking Logs:
- Go to your service in Render dashboard
- Click on "Logs" tab to see real-time application logs
- Look for startup errors or runtime exceptions

## Free Tier Limitations
- Service sleeps after 15 minutes of inactivity
- First request after sleep may take 30+ seconds
- 750 hours/month limit
- No persistent disk storage

## Production Recommendations
For a production deployment, consider:
- Upgrading to a paid plan for persistent PostgreSQL database
- Using a proper domain name
- Implementing proper error monitoring
- Setting up automated backups 
# Vercel Deployment Guide for Todo AI Chatbot

## Problem Diagnosis

The deployment issue was caused by incorrect Vercel configuration. The `vercel.json` file was using shell commands (`cd frontend &&`) which are **not supported** in Vercel's configuration fields.

### Error Chain
1. Initial Error: Vercel deploying old commit 9bf4ec1
   - **Root Cause**: Cache/timing issue (resolved by waiting for new deployment)

2. Current Error: `cd: frontend: No such file or directory`
   - **Root Cause**: Vercel doesn't support compound shell commands in config
   - **Solution**: Configure Root Directory in Vercel Dashboard + move vercel.json

## Solution Implemented

### Changes Made (Commit 2a9ce98)

1. **Moved vercel.json** from repository root to `frontend/` directory
2. **Simplified configuration** to remove shell commands
3. **Updated vercel.json** to standard Next.js format:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

## Required Vercel Dashboard Configuration

**CRITICAL**: You MUST configure the Root Directory in Vercel's dashboard. Here's how:

### Step 1: Access Project Settings

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: `Todo-Ai-Chatbot`
3. Click on **Settings** tab

### Step 2: Configure Root Directory

1. In Settings, navigate to **General** section
2. Scroll to **Root Directory** setting
3. Click **Edit** button
4. Enter: `frontend`
5. Check the box: **Include source files outside of the Root Directory in the Build Step**
6. Click **Save**

### Step 3: Redeploy

After saving the Root Directory setting:

#### Option A: Trigger New Deployment (Recommended)
1. Go to **Deployments** tab
2. Click the **three dots** menu on the latest deployment
3. Click **Redeploy**
4. Select **Use existing Build Cache: No** (important!)
5. Click **Redeploy** button

#### Option B: Push a New Commit
The latest commit (2a9ce98) should automatically trigger a new deployment with the correct configuration.

## Verification Steps

After redeploying, verify the build succeeds:

1. **Check Build Logs** - Should show:
   ```
   ✓ Running "install" command: npm install
   ✓ Detected Next.js version: 15.1.0
   ✓ Running "build" command: npm run build
   ```

2. **Check for Success Messages**:
   - ✓ No "cd: frontend: No such file or directory" error
   - ✓ Dependencies installed successfully
   - ✓ Build completed without errors

3. **Test the Deployment**:
   - Visit your Vercel deployment URL
   - Verify the frontend loads correctly
   - Check for any runtime errors in browser console

## Configuration Files

### Root Directory: `frontend/vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

### Frontend Package: `frontend/package.json`

Includes all required dependencies:
- Next.js 15.1.0
- React 19.0.0
- Better Auth 1.0.0
- Tailwind CSS 3.4.0
- TypeScript 5.7.0

## Common Issues and Solutions

### Issue 1: Still Deploying Old Commit

**Symptom**: Build logs show `Cloning ... (Commit: 9bf4ec1)` (old commit)

**Solution**:
1. Wait 30-60 seconds for GitHub webhook to trigger
2. Manually redeploy from Vercel dashboard
3. Ensure you're looking at the **latest** deployment in the list

### Issue 2: "No such file or directory" Error

**Symptom**: `sh: line 1: cd: frontend: No such file or directory`

**Solution**:
1. Ensure Root Directory is set to `frontend` in Vercel Settings
2. Ensure vercel.json is in `frontend/` directory (not root)
3. Clear build cache and redeploy

### Issue 3: Tailwind CSS Not Found

**Symptom**: Build fails with Tailwind CSS missing

**Solution**: This is fixed in commit 773ef8b which added:
```json
"devDependencies": {
  "tailwindcss": "^3.4.0",
  "postcss": "^8.4.0",
  "autoprefixer": "^10.4.0"
}
```

### Issue 4: Better Auth Import Error

**Symptom**: `Module not found: Can't resolve 'better-auth'`

**Solution**: This is fixed in commit 773ef8b which:
1. Changed import from `betterAuth` to `createAuthClient`
2. Added `better-auth` to dependencies in package.json

## Architecture Overview

```
Todo-Ai-Chatbot/
├── frontend/              # Next.js frontend (Vercel deployment)
│   ├── vercel.json       # Vercel configuration
│   ├── package.json      # Frontend dependencies
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/              # Utilities (auth, api)
│
├── backend/              # FastAPI backend (Render deployment)
│   ├── main.py
│   └── requirements.txt
│
└── render.yaml           # Render configuration for backend
```

## Deployment Workflow

### Frontend (Vercel)
1. Push changes to GitHub master branch
2. Vercel webhook triggers automatic deployment
3. Vercel clones repository
4. Vercel uses Root Directory setting to navigate to `frontend/`
5. Reads `frontend/vercel.json` for build configuration
6. Runs `npm install` → `npm run build`
7. Deploys to Vercel CDN

### Backend (Render)
1. Configured separately via render.yaml
2. Deploys FastAPI backend independently
3. Frontend connects via API endpoints

## Next Steps

1. **Configure Root Directory** in Vercel Dashboard (see Step 2 above)
2. **Redeploy** to apply the new configuration
3. **Monitor** the build logs for success
4. **Test** the deployed application
5. **Configure Environment Variables** in Vercel:
   - `NEXT_PUBLIC_API_URL` - Backend API URL
   - `NEXT_PUBLIC_BETTER_AUTH_URL` - Auth service URL

## Support Resources

- [Vercel Monorepo Documentation](https://vercel.com/docs/monorepos)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)
- [Vercel Build Configuration](https://vercel.com/docs/build-step)

## Commit History

- `2a9ce98` - fix: Move vercel.json to frontend directory and simplify configuration
- `da9efeb` - fix: Update vercel.json to build from frontend directory (obsolete approach)
- `773ef8b` - fix: Add Tailwind CSS dependencies and fix Better Auth import
- `9bf4ec1` - fix: Add missing frontend lib files to repository (old commit causing issues)

---

Generated: 2025-12-24
Status: Ready for deployment
Repository: https://github.com/codewithurooj/Todo-Ai-Chatbot

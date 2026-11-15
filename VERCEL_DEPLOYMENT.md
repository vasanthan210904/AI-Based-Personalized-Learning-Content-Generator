# Deploying LearnForge AI to Vercel

This repository is pre-configured for one-click serverless deployment to [Vercel](https://vercel.com) using `@vercel/python`.

---

## 🚀 Quick Deployment Steps

### Step 1: Import Repository on Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** → **"Project"**.
3. Select your GitHub repository:
   `vasanthan210904/AI-Based-Personalized-Learning-Content-Generator`
4. Leave **Framework Preset** as **Other** (Vercel automatically detects `vercel.json` and `api/index.py`).

---

### Step 2: Add Environment Variables
Under the **Environment Variables** section before deploying, add the following keys:

| Variable Name | Example / Value | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | `your-secret-encryption-key` | Session & CSRF encryption |
| `AI_PROVIDER` | `groq` | Primary AI engine |
| `GROQ_API_KEY` | `gsk_your_groq_api_key` | High-speed free generation |
| `GEMINI_API_KEY` | `your_gemini_api_key` | Google AI Studio fallback |
| `NVIDIA_API_KEY` | `nvapi_your_nvidia_key` | DeepSeek / NIM engine |
| `OPENROUTER_API_KEY` | `sk-or-your_openrouter_key` | Nemotron free models |
| `VERCEL` | `1` | Enables `/tmp/app.db` serverless SQLite storage |

---

### Step 3: Deploy
1. Click the **Deploy** button.
2. Vercel will install dependencies from `requirements.txt` and launch your serverless function via `api/index.py`.
3. Your live production URL will be ready in under 60 seconds (e.g. `https://ai-based-personalized-learning.vercel.app`).

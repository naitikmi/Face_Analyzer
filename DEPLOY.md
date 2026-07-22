# Deploying Atelier

Two services, deployed separately: the FastAPI backend (Render) and the Next.js
frontend (Vercel). Deploy the backend first — the frontend needs its URL at
build time.

## 1. Backend → Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in (GitHub login is easiest).
2. **New +** → **Web Service** → connect the `naitikmi/Face_Analyzer` GitHub repo.
3. Configure:
   - **Branch**: `main` (the repo's only branch — Render sometimes defaults to expecting `master`; pick `main` explicitly)
   - **Root Directory**: `backend`
   - **Environment**: `Docker` (Render auto-detects `backend/Dockerfile`)
   - **Instance Type**: Free is fine to start
   - **Auto-Deploy**: on (default) — this is what gives you "push to `main` → redeploys automatically"
4. Add environment variables (Render dashboard → Environment):
   - `GEMINI_API_KEY` — your key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (optional — only needed for "preview on me"; leave unset and that one feature just degrades gracefully)
   - `ALLOWED_ORIGINS` — leave as `http://localhost:3000` for now, you'll update this once the frontend is deployed (step 3 below)
5. Deploy. Note the resulting URL, e.g. `https://face-analyzer-backend.onrender.com`.
6. Confirm it's alive: visit `https://<your-render-url>/health` — should show `{"status":"ok"}`.

Free tier note: the service spins down after 15 minutes idle. The first request after a gap takes ~30-60s to wake it back up — normal, not a bug.

If the build itself fails: open the Render service → **Logs**, and paste the error back to me — I verified the Docker setup's dependency resolution carefully but couldn't run a live build myself (no container runtime available in my environment), so this is the one step I want to know about if it breaks.

## 2. Frontend → Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and sign in (GitHub login is easiest).
2. Import the `naitikmi/Face_Analyzer` repo.
3. Configure:
   - **Production Branch**: `main`
   - **Root Directory**: `frontend`
   - Framework preset: Next.js (auto-detected)
4. Add environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = your Render backend URL from step 1 (e.g. `https://face-analyzer-backend.onrender.com`) — no trailing slash
5. Deploy. Note the resulting URL, e.g. `https://face-analyzer.vercel.app`.

## 3. Close the loop: update backend CORS

Now that the frontend has a real URL:

1. Back in Render → your backend service → Environment.
2. Update `ALLOWED_ORIGINS` to your Vercel URL (e.g. `https://face-analyzer.vercel.app`). Multiple origins can be comma-separated if you also want to keep testing from elsewhere.
3. Save — Render redeploys automatically.

## 4. Use it on your phone

Open the Vercel URL on your phone's browser. Since it's real HTTPS (unlike plain `localhost`), the camera will work this time. To install as an app: use your browser's "Add to Home Screen" (Safari) or the install prompt (Chrome/Android).

## Redeploys

Both platforms auto-deploy on every push to `main` once connected — no extra steps needed after this initial setup.

# Deploying ContextGuard

The two halves go to different places:

| Part | Host | Why |
|---|---|---|
| React frontend (`frontend/`) | **Vercel** | Static site, free, deploys from GitHub |
| FastAPI backend (`backend/`) | **Hugging Face Spaces** (Docker, free CPU, 16 GB RAM) | PyTorch + ~520 MB of weights are far over Vercel's serverless size limit, and the models must stay loaded in memory |
| Trained weights | **Hugging Face Hub** model repo (private) | They're git-ignored; the backend downloads them on start |

Total cost: free. About 30 minutes, most of it waiting for builds.

---

## 1. Upload the trained models (once, from this PC)

1. Create an account at [huggingface.co](https://huggingface.co).
2. Create a **write** token: [Settings → Access Tokens](https://huggingface.co/settings/tokens).
3. Log in and upload:

```powershell
.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\python.exe -m backend.deploy.models upload --repo YOUR-NAME/contextguard-models
```

This uploads `transformer/`, `context_model/`, the `.joblib` models and the tokenizers (~530 MB) to a **private** model repo. Keep it private: the context model was trained partly on CONDA, which has no licence for redistribution.

Re-run the same command whenever you retrain a model.

## 2. Backend on a Hugging Face Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space):
   - Name: `contextguard-api`
   - SDK: **Docker** → Blank
   - Hardware: **CPU basic (free)**
   - Visibility: **Public** (the browser must be able to call it; the model repo stays private)
2. In the Space's **Files** tab, upload the two files from [`deploy/huggingface-space/`](deploy/huggingface-space/): `Dockerfile` and `README.md` (replace the existing README).
3. In the Space's **Settings → Variables and secrets**:

| Type | Name | Value |
|---|---|---|
| Variable | `MODEL_REPO` | `YOUR-NAME/contextguard-models` |
| Variable | `CORS_ORIGINS` | leave blank for now (set in step 4) |
| Secret | `HF_TOKEN` | a **read-only** token that can read the model repo |

   Don't set `HF_CHAT_MODEL` on a public demo: it would let anyone spend your Hugging Face credits.
4. Wait for the build (~10 minutes). Then open `https://YOUR-NAME-contextguard-api.hf.space/docs`. The startup log should say "Model artifacts ready". Send one analysis from the `/docs` page to load the models (the first request takes ~15 s).

The Space builds from the public GitHub repo's `main` branch. After you push new code, click **Settings → Factory rebuild**.

## 3. Frontend on Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and import the GitHub repo.
2. Set **Root Directory** to `frontend`. Vercel detects Vite; [`frontend/vercel.json`](frontend/vercel.json) sets the build command and output folder.
3. Add an environment variable:

| Name | Value |
|---|---|
| `VITE_API_URL` | `https://YOUR-NAME-contextguard-api.hf.space/api` |

4. Deploy. You get a URL like `https://contextguard.vercel.app`.

`VITE_*` values are compiled into the public JavaScript. Never put a token in one.

## 4. Connect them

Back in the Space settings, set `CORS_ORIGINS` to your Vercel URL (no trailing slash), e.g. `https://contextguard.vercel.app`. The Space restarts.

To also allow Vercel's preview deployments, set `CORS_ORIGIN_REGEX`, e.g. `https://contextguard-[a-z0-9-]+\.vercel\.app`.

Open the Vercel URL and analyse a sample conversation. If the page says it can't reach the API, check the browser console: a CORS error means `CORS_ORIGINS` doesn't exactly match the page's address.

---

## Things to know

- **Sleep:** a free Space sleeps after 48 hours without visits. The first request after that takes 1–2 minutes while it wakes and downloads the models. Open the Space a few minutes before a demo.
- **Speed:** models load on the first request (~15 seconds). After that, a 10-message conversation takes well under a second on CPU (0.35 s in a local test). No GPU needed.
- **Memory:** the backend uses about 450 MB of RAM with all models loaded. That's too close to the limit on 512 MB free tiers (Render, Railway); use a host with 1 GB or more.
- **State resets on restart:** custom Word2Vec models trained in the workbench live in memory only.
- **Privacy:** every analysed conversation is sent to the Space. Don't paste real private chats into a public demo.

## Other hosts

The root [`Dockerfile`](Dockerfile) builds the backend from your local checkout and runs on Render, Railway, Fly.io, Google Cloud Run or any VM with Docker:

```bash
docker build -t contextguard-api .
```

```bash
docker run -p 7860:7860 -e MODEL_REPO=YOUR-NAME/contextguard-models -e HF_TOKEN=hf_xxx -e CORS_ORIGINS=https://contextguard.vercel.app contextguard-api
```

Without `MODEL_REPO`, the server still starts, using only the rule engine and whatever models are in the image.

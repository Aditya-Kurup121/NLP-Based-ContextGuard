# Deploying ContextGuard (free, no card)

| Part | Host | Cost |
|---|---|---|
| React frontend (`frontend/`) | **Vercel** (Hobby) | Free |
| FastAPI backend (`backend/`) | **Render** free web service (Docker, 512 MB) | Free, no card |
| Trained weights (~530 MB, git-ignored) | **Hugging Face** private model repo in a team organization | Free |

Both Vercel and Render rebuild automatically on every push to `main`, so teammates with GitHub access update the live site just by pushing.

About 30 minutes, most of it waiting for builds.

---

## 1. Put the models on Hugging Face (once, from the PC that has them)

1. Create an account at [huggingface.co](https://huggingface.co).
2. **Team organization (recommended):** [huggingface.co/organizations/new](https://huggingface.co/organizations/new), e.g. `contextguard-team`, and invite teammates. Then everyone on the team can download or re-upload the models. Or use your own username instead.
3. Create a **Write** token at [Settings → Access Tokens](https://huggingface.co/settings/tokens).
4. In PowerShell, in the project folder:

```powershell
.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\python.exe -m backend.deploy.models upload --repo contextguard-team/contextguard-models
```

The repo is created **private**. Keep it that way: the context model was trained partly on CONDA, which has no licence for redistribution.

5. Create a second token, type **Read**, for the server. (Fine-grained tokens can be limited to this one repo.)

Teammates can get the models for local work with:

```powershell
.\.venv\Scripts\python.exe -m backend.deploy.models download --repo contextguard-team/contextguard-models
```

## 2. Backend on Render

1. Sign up at [render.com](https://render.com) with GitHub (no card needed).
2. **New → Blueprint**, pick the `NLP-Based-ContextGuard` repo. Render reads [`render.yaml`](render.yaml).
3. It asks for three values:

| Name | Value |
|---|---|
| `MODEL_REPO` | `contextguard-team/contextguard-models` |
| `HF_TOKEN` | the **Read** token |
| `CORS_ORIGINS` | `http://localhost:5173` for now (set the Vercel URL in step 4) |

4. **Apply**. The build takes ~10 minutes. You get a URL like `https://contextguard-api.onrender.com`.
5. Open `https://contextguard-api.onrender.com/docs` to check it's up.

## 3. Frontend on Vercel

1. [vercel.com/new](https://vercel.com/new) → sign in with GitHub → import the repo.
2. **Root Directory:** `frontend`. Vercel detects Vite; [`frontend/vercel.json`](frontend/vercel.json) has the build settings.
3. Environment variable `VITE_API_URL` = `https://contextguard-api.onrender.com/api`
4. **Deploy**. You get a URL like `https://contextguard.vercel.app`.

Never put a token in a `VITE_*` variable: they are compiled into the public JavaScript.

## 4. Connect them

In Render → `contextguard-api` → **Environment**, set `CORS_ORIGINS` to the Vercel URL, with no trailing slash (e.g. `https://contextguard.vercel.app`). Save; Render restarts the service.

Open the Vercel URL and analyse a sample conversation.

---

## What to expect on the free tier

Render's free instance has 512 MB of RAM and a tenth of a CPU core. All features work, including both DistilBERT models (tested under the same limits), but slowly:

| Situation | Time |
|---|---|
| Waking up after 15 minutes idle (download + load models) | 2–3 minutes |
| 6-message conversation, once awake | ~10 s |
| 40-message conversation | ~60 s |

**Before a demo or evaluation:** open `https://contextguard-api.onrender.com/docs` and run one analysis about 5 minutes ahead, then keep the tab active. The app keeps working while a request is slow; just wait for it.

The free settings are in [`render.yaml`](render.yaml): `TRANSFORMER_BATCH_SIZE=8`, `MALLOC_ARENA_MAX=2` and `OMP_NUM_THREADS=1` keep memory under 512 MB, and model calls are queued one at a time.

Other notes:
- Custom Word2Vec models trained in the workbench are lost when the service restarts.
- Every analysed conversation is sent to the server. Don't paste real private chats into a public demo.
- Don't set `HF_CHAT_MODEL` on a public deployment: anyone could spend your Hugging Face credits.
- Logs: Render → `contextguard-api` → **Logs**. "Model artifacts ready" means the download worked.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Page says it can't reach the API; browser console shows a CORS error | `CORS_ORIGINS` must exactly match the Vercel address (https, no trailing slash) |
| Results show no DistilBERT scores | Check the Render log for the model download; `MODEL_REPO` or `HF_TOKEN` is wrong |
| Very slow first request | Normal after idle: the service is waking up |

## Faster options (not free)

- **Google Cloud Run** (needs a card; free tier, plus ~$0.20/month image storage): `powershell -ExecutionPolicy Bypass -File deploy\deploy-cloudrun.ps1 -Project YOUR-PROJECT-ID -ModelRepo contextguard-team/contextguard-models`. Install the CLI with `winget install Google.CloudSDK` and run `gcloud init` first. Under a second per conversation once warm.
- **Hugging Face Spaces** (PRO, $9/month): upload the two files in [`deploy/huggingface-space/`](deploy/huggingface-space/) to a Docker Space.
- **Any Docker host** with 1 GB+ RAM: `docker build -t contextguard-api .` using the root [`Dockerfile`](Dockerfile).

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.app.api.routes import router
from backend.app.api.nlp_routes import router as nlp_router
from backend.app.api.import_routes import router as import_router

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ContextGuard")

app = FastAPI(
    title="ContextGuard API",
    description="Context-Aware Cyberbullying and Conversational Risk Detection Engine",
    version="1.2.0"
)

# CORS: only the configured frontend origins may call the API from a browser.
# The API uses no cookies, so credentials are not allowed.
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
app.include_router(nlp_router)
app.include_router(import_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred during conversational analysis."}
    )

@app.get("/")
def root():
    return {
        "name": "ContextGuard API",
        "tagline": "Understand the context. Detect the harm.",
        "documentation": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), reload=True)

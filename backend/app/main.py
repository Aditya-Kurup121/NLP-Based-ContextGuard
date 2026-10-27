from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.app.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ContextGuard")

app = FastAPI(
    title="ContextGuard API",
    description="Context-Aware Cyberbullying and Conversational Risk Detection Engine",
    version="1.2.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow frontend Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

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
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

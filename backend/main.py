from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import Base, engine

# Import all route modules 
from routes.auth import router as auth_router
from routes.mood import router as mood_router
from routes.chat import router as chat_router
from routes.journal import router as journal_router
from routes.assessment import router as assessment_router
from routes.emotion import router as emotion_router

# Create all DB tables 
Base.metadata.create_all(bind=engine)

# App instance 
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow React Native / Expo dev client 
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(mood_router)
app.include_router(chat_router)
app.include_router(journal_router)
app.include_router(assessment_router)
app.include_router(emotion_router)


# Health check 
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
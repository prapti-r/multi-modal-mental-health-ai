from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import engine
from core.exceptions import register_exception_handlers
from core.redis import close_redis, init_redis
import models  # noqa: F401 — side-effect: registers all ORM classes with Base.metadata
from models.base import Base

from routes.auth import router as auth_router
from routes.auth import user_router as auth_user_router
from routes.user import router as user_profile_router
from routes.mood import router as mood_router
from routes.journal import router as journal_router
from routes.assessments import router as assessments_router
from routes.assessments import risk_router
from routes.chat import router as chat_router
from routes.reports import router as reports_router

from admin import create_admin

@asynccontextmanager
async def lifespan(app: FastAPI):

    #  Startup 
    await init_redis()

    from ml import bert_classifier, facial_emotion, speech_emotion
 
    bert_classifier.load_model()
    speech_emotion.load_models(whisper_size="base")
    facial_emotion.load_model()

    # Create tables for local dev; use Alembic migrations in production
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    #  Shutdown 
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,   
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Middleware 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers 
    register_exception_handlers(app)

    #  Routers 
    
    PREFIX = settings.API_V1_PREFIX

    app.include_router(auth_router, prefix=PREFIX)  # POST /auth/*
    app.include_router(auth_user_router, prefix=PREFIX)  # PUT  /user/change-password
                                                             # DEL  /user/account
    app.include_router(user_profile_router, prefix=PREFIX)  # GET/PATCH /user/profile
                                                             # GET/PUT   /user/settings
 
    # Daily tracking 
    app.include_router(mood_router,  prefix=PREFIX)  # POST /mood/log
                                                             # GET  /mood/history
    app.include_router(journal_router, prefix=PREFIX)  # POST /journal/entry
                                                             # GET  /journal/history
                                                             # GET  /journal/entry/{id}
 
    # Assessments & risk 
    app.include_router(assessments_router, prefix=PREFIX)  # POST /assessments/submit
                                                             # GET  /assessments/history
    app.include_router(risk_router, prefix=PREFIX)  # GET  /risk/history
 
    # Chat engine 
    app.include_router(chat_router, prefix=PREFIX)  # POST /chat/session
                                                             # GET  /chat/sessions
                                                             # POST /chat/message
                                                             # POST /chat/message/media
                                                             # GET  /chat/sessions/{id}/messages
 
    # Reports & directory 
    app.include_router(reports_router, prefix=PREFIX)  # GET  /reports/weekly
                                                             # GET  /therapists
 
    # Health
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}
 
    return app
 
 
app = create_app()

create_admin(app)
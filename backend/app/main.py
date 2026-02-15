from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes_auth import router as auth_router
from app.routes_chat import router as chat_router

from app.api.diseases import router as diseases_router
from app.api.symptom_checker import router as symptom_router

from app.database import Base, engine
from app import models  # ✅ IMPORTANT: load models so tables register
from app.api.quiz import router as quiz_router
from app.api.reports import router as reports_router
from app.api.feedback import router as feedback_router



# ✅ Create DB tables (users, chats, messages, documents)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Health Assistant API")

# ✅ OPTIONAL: Disable ingest during development (faster startup)
# from app.rag.ingest import ingest_folder_to_pinecone
# @app.on_event("startup")
# def startup_ingest():
#     ingest_folder_to_pinecone()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        settings.FRONTEND_BASE_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Required for sessions (OAuth / cookies)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

app.include_router(auth_router)
app.include_router(chat_router)

app.include_router(diseases_router)
app.include_router(symptom_router)

app.include_router(quiz_router)
app.include_router(reports_router)
app.include_router(feedback_router)
#app.include_router(feedback_router)
from app.api.ml_prediction import router as ml_router
app.include_router(ml_router)


@app.get("/")
def root():
    return {"message": "API running"}

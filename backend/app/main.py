# backend/app/main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1_rico import router as rico_router

app = FastAPI(
    title="Rico 4.0 Orchestrator",
    docs_url="/api/v1/docs",        # Swagger
    redoc_url="/api/v1/redoc"       # Redoc (optional)
)

# CORS für Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "agent": "Rico 4.0"}

# Router einbinden
app.include_router(rico_router, prefix="/api/v1")
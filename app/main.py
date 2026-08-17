from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.routers import cases, legal
from app.rag.seed_kb import seed_database
from app.services import case_service
from app.schemas import SystemStatsResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema exists
    Base.metadata.create_all(bind=engine)
    # Seed default legal chunks and initialize BM25 index
    try:
        seed_database()
    except Exception as e:
        print(f"Startup knowledge base seeding notice: {e}")
    yield


app = FastAPI(
    title="Civic RTI Drafter API",
    description="Deterministic local-first Civic RTI and First Appeal drafting engine with BM25 legal grounding.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(legal.router)


@app.get("/", tags=["system"])
def root():
    return {
        "message": "Civic RTI Drafter API is active",
        "docs_url": "/docs",
        "disclaimer": "This is a drafting assistant and does not provide legal advice.",
    }


@app.get("/stats", response_model=SystemStatsResponse, tags=["system"])
def get_stats(db: Session = Depends(get_db)):
    return case_service.get_system_stats(db)

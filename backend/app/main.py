from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def _ensure_schema_upgrades() -> None:
    """create_all 不会给已有表补列，这里做幂等的增量补列。"""
    inspector = inspect(engine)
    if "products" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("products")}
        if "proof_off_oven" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE products ADD COLUMN proof_off_oven BOOLEAN NOT NULL DEFAULT FALSE")
                )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_schema_upgrades()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BakeOven", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.routers import ask, index


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    db.ensure_schema()
    yield


app = FastAPI(title="rag-all-stack AI 服务", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask.router)
app.include_router(index.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

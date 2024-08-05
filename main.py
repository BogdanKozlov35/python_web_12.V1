import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from src.admin import route_admin
from src.auth import route_auth

from src.database.db import get_db
from src.contacts import route_contacts
from src.conf.config import config

import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Contact Management API", description="API для зберігання та управління контактами")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(route_contacts.router, tags=["contacts"])
app.include_router(route_admin.router, tags=["admin"])
app.include_router(route_auth.router, tags=["authentication"])


@app.on_event("startup")
async def startup():
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )

    await FastAPILimiter.init(r)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def index():
    return {"msg": "Hello World"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")

# logging.info("Registered routes:")
# for route in app.routes:
#     logging.info(f"Route: {route.path}, name: {route.name}")

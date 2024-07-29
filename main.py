from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import route_auth
from src.database.db import get_db
from src.contacts import route_contacts

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
app.include_router(route_auth.router, tags=["admin"])
app.include_router(route_auth.router, tags=["authentication"])

@app.get("/")
def index():
    return {"message": "Contacts Application"}


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
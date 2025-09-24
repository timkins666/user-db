"""initialise the FastAPI app"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from userdb import db
from userdb.routers import users


@asynccontextmanager
async def lifespan(_: FastAPI):
    """lifespan handler for DB. Initialises tables at startup."""
    db.init_db()
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(users.router)


@app.get("/", status_code=200)
async def root():
    """root url - pseudo healthcheck"""
    return "OK :)"

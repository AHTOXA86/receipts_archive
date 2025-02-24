from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routes.user import router as user_router
from app.routes.receipt import router as receipt_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Include user routes
app.include_router(user_router)
app.include_router(receipt_router)

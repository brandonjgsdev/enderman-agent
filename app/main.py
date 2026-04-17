from fastapi import FastAPI
from app.routers import conversations

app = FastAPI()

app.include_router(conversations.router)
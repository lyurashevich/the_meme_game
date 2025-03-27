from fastapi import FastAPI
from handlers import router as ws_router
from security.handlers import router as token_router

app = FastAPI()

app.include_router(ws_router)
app.include_router(token_router)

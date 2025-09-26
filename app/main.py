from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.db import session_maker
from app.services.memes_services import CardService as MemeService
from app.services.situations_services import CardService as SituationService
from app.views.game import router as game_router
from app.views.meme_cards_views import router as memes_router
from app.views.players_views import router as players_router
from app.views.room_views import router as rooms_router
from app.views.round import router as game_round_router
from app.views.situation_cards_views import router as situations_router
from app.websockets.views import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    with session_maker() as db:
        MemeService(db)
        SituationService(db)
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(memes_router)
app.include_router(situations_router)
app.include_router(players_router)
app.include_router(rooms_router)
app.include_router(ws_router)
app.include_router(game_router)
app.include_router(game_round_router)

templates = Jinja2Templates(directory="templates")


@app.get("/ws", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

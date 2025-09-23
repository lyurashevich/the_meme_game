from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.views.meme_cards_views import router as memes_router
from app.views.players_views import router as players_router
from app.views.room_views import router as rooms_router
from app.views.situation_cards_views import router as situations_router
from app.websockets.views import router as ws_router

app = FastAPI()

app.include_router(memes_router)
app.include_router(situations_router)
app.include_router(players_router)
app.include_router(rooms_router)
app.include_router(ws_router)

templates = Jinja2Templates(directory="templates")


@app.get("/ws", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

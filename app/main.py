from fastapi import FastAPI

from app.views.meme_cards_views import router as memes_router
from app.views.players_views import router as players_router
from app.views.room_views import router as rooms_router
from app.views.situation_cards_views import router as situations_router

app = FastAPI()

app.include_router(memes_router)
app.include_router(situations_router)
app.include_router(players_router)
app.include_router(rooms_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

import logging

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.config import get_settings
from app.exceptions import CustomException
from app.views.game import router as game_router
from app.views.health import router as health_router
from app.views.meme_cards_views import router as memes_router
from app.views.players_views import router as players_router
from app.views.room_views import router as rooms_router
from app.views.round import router as game_round_router
from app.views.situation_cards_views import router as situations_router
from app.websockets.views import router as ws_router

logging.basicConfig(
    level=get_settings().log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI()


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exception: CustomException):
    return JSONResponse(
        status_code=exception.status_code, content={"error": {"code": exception.code, "message": exception.message}}
    )


app.include_router(health_router)
app.include_router(memes_router)
app.include_router(situations_router)
app.include_router(players_router)
app.include_router(rooms_router)
app.include_router(ws_router)
app.include_router(game_router)
app.include_router(game_round_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104

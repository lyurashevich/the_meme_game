from api.cards import router as cards_router
from fastapi import FastAPI

app = FastAPI()

app.include_router(cards_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

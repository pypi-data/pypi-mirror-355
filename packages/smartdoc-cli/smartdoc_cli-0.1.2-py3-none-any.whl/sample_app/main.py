from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.post("/items", response_model=Item, summary="Create item")
def create_item(item: Item):
    return item

from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

from typing import Optional

app = FastAPI()

weight = [("a", 1), ("b", 2), ("c", 3)]
score = [1, 2, 3, 4, 5]


class Item(BaseModel):
    name: str
    weight_type: str
    score: int


fake_table: dict[str, Item] = {}


@app.get("/items/{name:str}", response_model=Item)
def get_item_by_name(name: str = Path()):
    return fake_table[name]


@app.post("/items")
def add_new_item(data: Item):
    fake_table[data.name] = data


@app.get("/items")
def list_item(weight_type: Optional[str] = Query()):
    if weight_type:
        return list(
            filter(lambda i: i.weight_type == weight_type, fake_table.values())
        )
    else:
        return list(fake_table.values())

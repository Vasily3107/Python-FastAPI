from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

app = FastAPI(
    title = 'Game Store',
    description = 'Buy and Sell games!',
    version = '1.0.0'
)


class GameCreate(BaseModel):
    model_config = ConfigDict(extra = 'forbid')

    title: str   = Field(min_length = 2, max_length = 100)
    genre: str   = Field(min_length = 2, max_length = 100)
    price: float = Field(ge = 0)

class GameUpdate(BaseModel):
    model_config = ConfigDict(extra = 'forbid')

    title: str   | None = Field(min_length = 2, max_length = 100, default = None)
    genre: str   | None = Field(min_length = 2, max_length = 100, default = None)
    price: float | None = Field(ge = 0, default = None)


games = [
    {
        'id': 1,
        'title': 'Manifold Garden',
        'genre': 'Puzzle',
        'price': 4.99,
    },
    {
        'id': 2,
        'title': 'Ready or Not',
        'genre': 'FPS',
        'price': 9.99,
    },
    {
        'id': 3,
        'title': 'Cuphead',
        'genre': 'Platformer',
        'price': 4.99,
    },
]

def new_id() -> int:
    global games
    return 1 + max([i['id'] for i in games])

def game_with_id(id: int) -> dict | None:
    global games
    return next((i for i in games if i['id'] == id), None)

def title_exists(title: str) -> bool:
    global games
    return bool(len([i for i in games if i['title'].lower() == title.lower()]))


@app.get('/')
def root():
    return { 'message': 'Home page' }

@app.get('/games')
def get_all_games(
    genre: Annotated[str | None, Query(min_length = 1)] = None,
    min_price: Annotated[float | None, Query(ge = 0)] = None,
    max_price: Annotated[float | None, Query(ge = 0)] = None,
    search: Annotated[str | None, Query(min_length = 1)] = None,
    ):
    global games

    if min_price and max_price and min_price > max_price:
        return HTTPException(400, 'min_price cannot be greater than max_price')

    res = games

    if search:    res = [i for i in res if search.lower() in i['title'].lower()]
    if genre:     res = [i for i in res if i['genre'].lower() == genre.lower()]
    if min_price: res = [i for i in res if i['price'] >= min_price]
    if max_price: res = [i for i in res if i['price'] <= max_price]

    return res

@app.get('/games/{id}')
def get_game_by_id(id: int):
    global games

    if game := game_with_id(id):
        return game

    return HTTPException(404, 'Game not found')

@app.post('/games')
def add_game(game: GameCreate):
    global games

    if title_exists(game.title):
        return HTTPException(400, 'Game with this title already exists')

    games.append(new_game := {
        'id': new_id(),
        **game.model_dump()
    })
    return new_game

@app.patch('/games/{id}')
def update_game(id: int, update: GameUpdate):
    global games

    update: dict = {k: v for k, v in update.model_dump().items() if v is not None}

    if not len(update):
        return HTTPException(400, 'No update fields were provided')

    if (game := game_with_id(id)) is None:
        return HTTPException(404, 'Game not found')

    if update.get('title', None) and title_exists(update['title']):
        return HTTPException(400, 'Game with this title already exists')

    game |= update
    games[games.index(game)] = game
    return game

@app.delete('/games/{id}')
def delete_game(id: int):
    global games

    if game := game_with_id(id):
        games.pop(games.index(game))
        return game
    else:
        return HTTPException(404, 'Game not found')
    
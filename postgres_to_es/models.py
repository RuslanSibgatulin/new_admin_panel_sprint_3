import uuid
from pydantic import BaseModel, Field, validator


class Person(BaseModel):
    id: uuid.UUID
    name: str


class Movie(BaseModel):
    id: uuid.UUID
    imdb_rating: float = Field(alias='rating')
    title: str
    description: str
    genre: str
    director: str
    actors: list[dict]
    actors_names: str
    writers: list[dict]
    writers_names: str

    @validator('*', pre=True)
    def set_director(cls, name):
        return name or 'N/A'

    @validator('description')
    def set_desc(cls, name):
        return str(name).replace('"', '')

    @validator('actors', 'writers', pre=True)
    def persons_must_be_list(cls, v):
        pers = [{}]
        if isinstance(v, dict):
            pers = list(map(
                lambda x: {'id': x, 'name': v[x]}, v))
        return pers

import uuid
from pydantic import BaseModel, Field, validator


class Person(BaseModel):
    id: uuid.UUID
    name: str


class Movie(BaseModel):
    """https://pydantic-docs.helpmanual.io/usage/schema/#field-customization"""
    id: uuid.UUID
    imdb_rating: float = Field(alias='rating', ge=0, le=10)
    title: str
    description: str
    genre: list[str]
    director: list[str]
    actors: list[dict]
    actors_names: list[str]
    writers: list[dict]
    writers_names: list[str]

    @validator('description')
    def set_desc(cls, name):
        return str(name).replace('"', '')

    @validator('description', pre=True)
    def set_name(cls, name):
        return name or ''

    @validator('imdb_rating', pre=True)
    def set_rating(cls, value):
        return value or 0

    @validator('genre', pre=True)
    def set_genre(cls, value):
        return value or ['N/A']

    @validator('actors_names', 'writers_names', 'director', pre=True)
    def names_must_be_list(cls, value):
        return value or []

    @validator('actors', 'writers', pre=True)
    def persons_must_be_list_of_dict(cls, v):
        pers = [{}]
        if isinstance(v, dict):
            pers = list(map(
                lambda x: {'id': x, 'name': v[x]}, v))
        return pers

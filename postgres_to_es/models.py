from typing import Optional
from uuid import UUID, uuid3
from pydantic import BaseModel, Field, validator, BaseSettings


class UUIDMixin(BaseModel):
    uuid: UUID = Field(alias='id')


class Genre(UUIDMixin):
    name: str


class Person(UUIDMixin):
    full_name: str
    role: str
    film_ids: list[UUID]
    doc_id: Optional[UUID]

    @validator('doc_id', always=True)
    def fill_doc_id(cls, value, values):
        id, role = values["uuid"], values["role"]
        return uuid3(id, role)

    @validator('film_ids', pre=True)
    def film_ids_must_be_list_of_uuid(cls, v):
        if isinstance(v, str):
            return v[1:-1].split(',')


class Movie(UUIDMixin):
    """https://pydantic-docs.helpmanual.io/usage/schema/#field-customization"""
    imdb_rating: float = Field(alias='rating', ge=0, le=10)
    title: str
    description: str
    genre: list[dict]  # dict
    directors: list[dict]  # dict
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

    @validator('actors_names', 'writers_names', pre=True)
    def names_must_be_list(cls, value):
        return value or []

    @validator('actors', 'writers', 'directors', 'genre', pre=True)
    def persons_must_be_list_of_dict(cls, v):
        pers = [{}]
        if isinstance(v, dict):
            pers = list(map(
                lambda x: {'id': x, 'name': v[x]}, v))
        return pers


class Postgres_dsn(BaseSettings):
    host: str = Field(env="POSTGRES_HOST")
    port: int = Field(env="POSTGRES_PORT")
    user: str = Field(env="POSTGRES_USER")
    password: str = Field(env="POSTGRES_PASSWORD")
    dbname: str = Field(env="POSTGRES_DB")
    options: str = Field('-c search_path=content')

    class Config:
        env_file = '.env'

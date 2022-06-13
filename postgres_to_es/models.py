from uuid import UUID
from pydantic import BaseModel, Field, validator, BaseSettings


class NameMixin(BaseModel):
    uuid: UUID = Field(alias='id')
    name: str


class Movie(BaseModel):
    """https://pydantic-docs.helpmanual.io/usage/schema/#field-customization"""
    uuid: UUID = Field(alias='id')
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

    # @validator('genre', pre=True)
    # def set_genre(cls, value):
    #     return value or ['N/A']

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

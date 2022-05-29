import json
import os
import logging
import logging.config
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
from elasticsearch7 import Elasticsearch

from psycopg2 import connect as _pg_conn

from models import Movie
from json_storage import JsonFileStorage, State
from es_loader import ElasticsearchMovies
from pg_movies import PostgresMovies


def etl(es: ElasticsearchMovies, pg: PostgresMovies, sync_interval: int = 60):
    """
    Основной процесс загрузки-выгрузки.
    """
    state = State(JsonFileStorage('state.json'))
    logger.debug('Start ETL process')
    while True:
        try:
            pg_data = pg.modified_movies(state.get_state('etl_state'))
            es_data = [
                {
                    '_index': 'movies',
                    '_id': i['id'],
                    '_source': Movie.parse_obj(i).dict(),
                }
                for i in pg_data
            ]
            logger.debug('%s', es_data)
            es_movies.bulk(es_data)

            # state.set_state('etl_state', datetime.now().isoformat())
            break
            sleep(sync_interval)  # wait next updates

        except KeyboardInterrupt:
            logger.debug('Interrupted')
            break


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('logger')

    load_dotenv()
    dsn = {
        "host": os.environ.get("POSTGRES_HOST"),
        "port": os.environ.get("POSTGRES_PORT"),
        "user": os.environ.get("POSTGRES_USER"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
        "dbname": os.environ.get("POSTGRES_DB"),
        'options': '-c search_path=content',
    }

    with _pg_conn(**dsn) as pg_conn:
        pg_movies = PostgresMovies(pg_conn)

    with open('elasticsearch/es_schema.json', 'r') as idx:
        index_body = json.loads(idx.read())

    es_movies = ElasticsearchMovies(
        Elasticsearch(os.environ.get("ES_HOST")),
        index_body
    )

    etl(es_movies, pg_movies)

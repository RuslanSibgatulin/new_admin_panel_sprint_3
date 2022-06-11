import os
import logging.config
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
from elasticsearch7 import Elasticsearch

from models import Postgres_dsn, Movie, NameMixin
from json_storage import JsonFileStorage, State
from es_loader import ElasticsearchMovies
from pg_movies import PostgresMovies


def loop(pg: PostgresMovies, es: ElasticsearchMovies):
    """Цикл жизни ETL."""
    state = State(JsonFileStorage('state.json'))
    sync_interval = int(os.environ.get("ETL_INTERVAL", 60))
    es_indexes = {
        'movies': {
            'getter': pg.modified_movies,
            'coverter': Movie,
        },
        'genres': {
            'getter': pg.modified_genres,
            'coverter': NameMixin,
        },
        'persons': {
            'getter': pg.modified_persons,
            'coverter': NameMixin
        }
    }

    logger.info('Start ETL process')
    while True:
        try:
            etl(es, es_indexes, state)
        except KeyboardInterrupt:
            logger.error('Interrupted')
            break
        except Exception as err:
            logger.error('%s', err)
        finally:
            logger.debug('Wait next updates %d sec', sync_interval)
            sleep(sync_interval)


def etl(
    es: ElasticsearchMovies,
    es_indexes: dict,
    state: JsonFileStorage
):
    """Основной процесс порционной выгрузки - загрузки."""

    since = state.get_state('etl_state') or datetime.min
    start = datetime.utcnow()
    logger.debug('Get data from postgres since %s', since)

    for idx, meta in es_indexes.items():
        page = meta.get('getter')(since)
        pg_data = next(page, [])
        while pg_data:
            es_data = transform(idx, meta.get('coverter'), pg_data)
            es.bulk(es_data)
            logger.debug('Loaded: %s', es_data)
            logger.info(
                '%d docs loaded. Total time: %s',
                len(pg_data),
                datetime.utcnow() - start
            )
            pg_data = next(page, [])

    # save state
    state.set_state('etl_state', start.isoformat())


def transform(index_name, _class, pg_data):
    """Преобразование Postgres данных в формат для записи Elasticsearch."""
    es_data = [
            {
                '_index': index_name,
                '_id': i['id'],
                '_source': _class.parse_obj(i).dict(),
            }
            for i in pg_data
        ]

    return es_data


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('ETL')

    load_dotenv()
    pg_movies = PostgresMovies(
        dsn=Postgres_dsn().dict(),
        limit=os.environ.get("LIMIT", 500)
    )
    es_movies = ElasticsearchMovies(
        Elasticsearch(os.environ.get("ES_HOST"))
    )

    loop(pg_movies, es_movies)

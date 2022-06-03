import os
import logging.config
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
from elasticsearch7 import Elasticsearch

from models import Movie, Postgres_dsn
from json_storage import JsonFileStorage, State
from es_loader import ElasticsearchMovies
from pg_movies import PostgresMovies


def loop(pg: PostgresMovies, es: ElasticsearchMovies):
    """Цикл жизни ETL."""
    state = State(JsonFileStorage('state.json'))
    limit = int(os.environ.get("LIMIT", 1000))
    sync_interval = int(os.environ.get("ETL_INTERVAL", 60))
    logger.info('Start ETL process. Load limit %d', limit)
    while True:
        try:
            etl(es, pg, state, limit)
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
    pg: PostgresMovies,
    state: JsonFileStorage,
    limit: int
):
    """Основной процесс порционной выгрузки - загрузки."""
    since = state.get_state('etl_state') or datetime(1, 1, 1)
    start = datetime.utcnow()
    logger.debug('Get pg_data since %s', since)
    page = pg.modified_movies(since, limit)
    pg_data = next(page, [])
    while pg_data:
        es_data = transform(pg_data)
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


def transform(pg_data):
    """Преобразование Postgres данных в формат для записи Elasticsearch."""
    es_data = [
            {
                '_index': 'movies',
                '_id': i['id'],
                '_source': Movie.parse_obj(i).dict(),
            }
            for i in pg_data
        ]

    return es_data


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('ETL')

    load_dotenv()
    pg_movies = PostgresMovies(Postgres_dsn().dict())
    es_movies = ElasticsearchMovies(
        Elasticsearch(os.environ.get("ES_HOST"))
    )

    loop(pg_movies, es_movies)

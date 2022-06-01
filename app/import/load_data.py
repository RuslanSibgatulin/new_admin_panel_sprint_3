import logging
import logging.config
import os
import sqlite3
from sqlite3 import connect as _sq_conn
from psycopg2 import connect as _pg_conn
from sqliteloader import SQLiteLoader
from postgressaver import PostgresSaver
from contextlib import contextmanager


SQLITE_SCHEMA = {
    "genre": ("id", "name", "description", "created_at", "updated_at"),
    "film_work": (
        "id", "title", "description", "creation_date",
        "rating", "type", "created_at", "updated_at"
    ),
    "person": ("id", "full_name", "created_at", "updated_at"),
    "genre_film_work": ("id", "film_work_id", "genre_id", "created_at"),
    "person_film_work": (
        "id", "film_work_id", "person_id", "role", "created_at"
    )
}

PG_SCHEMA = {
    "genre": ("id", "name", "description", "created", "modified"),
    "film_work": (
        "id", "title", "description", "creation_date",
        "rating", "type", "created", "modified"
    ),
    "person": ("id", "full_name", "created", "modified"),
    "genre_film_work": ("id", "film_work_id", "genre_id", "created"),
    "person_film_work": (
        "id", "film_work_id", "person_id", "role", "created"
    )
}


def load_from_sqlite(connection: _sq_conn, pg_conn: _pg_conn):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    for table in SQLITE_SCHEMA:
        try:
            logging.debug('Loading table %s', table)
            page = sqlite_loader.loader(table, SQLITE_SCHEMA[table])
            row_count = 0
            while True:
                data = next(page)
                row_count += len(data)
                postgres_saver.save_data(table, PG_SCHEMA[table], data)
        except StopIteration:
            logging.debug("Done! Rows count: %d", row_count)
        except BaseException as err:
            logging.error("%s load error - %s", table, err)


@contextmanager
def open_sqlite(file_name: str):
    connection = _sq_conn(file_name)
    try:
        yield connection
    except sqlite3.DatabaseError as err:
        logging.error(err)
    finally:
        connection.close()


if __name__ == "__main__":
    logging.config.fileConfig('logging.conf')

    db_sqlite = os.environ.get("DB_SQLITE", 'db.sqlite')
    dsn = {
        "dbname": os.environ.get("POSTGRES_DB"),
        "user": os.environ.get("POSTGRES_USER"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
        "host": os.environ.get("POSTGRES_HOST"),
        "port": os.environ.get("DB_PORT", 5432),
        'options': '-c search_path=content',
    }

    with open_sqlite(db_sqlite) as sqlite_conn, _pg_conn(**dsn) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)

import psycopg2
import logging
from datetime import datetime
from psycopg2.extensions import connection as pg_connect, STATUS_READY
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from backoff import backoff


@dataclass
class PostgresMovies:
    dsn: dict
    conn: pg_connect = None

    @backoff('PostgresMovies.connect', 0.3)
    def connect(cls) -> bool:
        if not cls.conn or cls.conn.status != STATUS_READY:
            cls.conn = psycopg2.connect(**cls.dsn)

        return True

    def modified_movies(cls, since: datetime, limit: int = 100):
        query = """
            SELECT
            fw.id, fw.title, fw.description, fw.rating,

            jsonb_object_agg(DISTINCT person.id, person.full_name )
                FILTER (WHERE person_film_work.role = 'actor') AS actors,
            array_agg(DISTINCT person.full_name)
                FILTER (WHERE person_film_work.role = 'actor') AS actors_names,
            jsonb_object_agg(DISTINCT person.id, person.full_name )
                FILTER (WHERE person_film_work.role = 'writer') AS writers,
            array_agg(DISTINCT person.full_name)
                FILTER (WHERE person_film_work.role='writer') AS writers_names,
            array_agg(DISTINCT person.full_name)
                FILTER (WHERE person_film_work.role = 'director') AS director,
            array_agg(DISTINCT genre.name) AS genre

            FROM film_work as fw
            LEFT OUTER JOIN genre_film_work
                ON (fw.id = genre_film_work.film_work_id)
            LEFT OUTER JOIN genre
                ON (genre_film_work.genre_id = genre.id)
            LEFT OUTER JOIN person_film_work
                ON (fw.id = person_film_work.film_work_id)
            LEFT OUTER JOIN person
                ON (person_film_work.person_id = person.id)

            WHERE fw.id in
            (
                SELECT film_work.id FROM film_work
                WHERE film_work.modified > '{0}'

                UNION DISTINCT SELECT pfw.film_work_id FROM person
                LEFT OUTER JOIN person_film_work pfw
                    ON (person.id = pfw.person_id)
                WHERE person.modified > '{0}'

                UNION DISTINCT SELECT gfw.film_work_id FROM genre
                LEFT OUTER JOIN genre_film_work gfw
                    ON (genre.id = gfw.genre_id)
                WHERE genre.modified > '{0}'
            )
            GROUP BY fw.id;
            """.format(since)

        if cls.connect():
            with cls.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                while True:
                    page = cur.fetchmany(limit)
                    if page:
                        yield list(map(dict, page))
                    else:
                        break

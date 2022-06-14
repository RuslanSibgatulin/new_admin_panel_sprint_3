import psycopg2
from datetime import datetime
from psycopg2.extensions import connection as pg_connect, STATUS_READY
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from backoff import backoff


@dataclass
class PostgresMovies:
    dsn: dict
    conn: pg_connect = None
    limit: int = 1000

    @backoff('PostgresMovies.connect')
    def connect(cls) -> bool:
        if not cls.conn or cls.conn.status != STATUS_READY:
            cls.conn = psycopg2.connect(**cls.dsn)

        return True

    def get_limited_data(cls, query: str):
        if cls.connect():
            with cls.conn.cursor(cursor_factory=RealDictCursor) as cur:
                offset = 0
                while True:
                    limited_query = '{0} LIMIT {1} OFFSET {2}'.format(
                        query, cls.limit, offset)
                    cur.execute(limited_query)

                    page = cur.fetchall()
                    if page:
                        offset += len(page)
                        yield list(map(dict, page))
                    else:
                        break

    def modified_movies(cls, since: datetime):
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
            jsonb_object_agg(DISTINCT person.id, person.full_name )
                FILTER (WHERE person_film_work.role = 'director') AS directors,
            jsonb_object_agg(DISTINCT genre.id, genre.name) AS genre

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
            GROUP BY fw.id
            """.format(since)
        yield from cls.get_limited_data(query)

    def modified_persons(cls, since: datetime):
        query = """
            SELECT DISTINCT pfw.person_id "id", person.full_name "name"
            FROM person_film_work pfw
            JOIN person ON person.id = pfw.person_id
            WHERE person.modified > '{0}'
        """.format(since)
        yield from cls.get_limited_data(query)

    def modified_genres(cls, since: datetime):
        query = """
            SELECT DISTINCT gfw.genre_id "id", genre.name "name"
            FROM genre_film_work gfw
            JOIN genre ON genre.id = gfw.genre_id
            WHERE genre.modified > '{0}'
        """.format(since)
        yield from cls.get_limited_data(query)

    def modified_persons_by_role(cls, since: datetime):
        query = """
            SELECT
            pfw.person_id id,
            person.full_name, pfw.role,
            array_agg(pfw.film_work_id) AS film_ids
            FROM person_film_work pfw
            JOIN film_work fw ON fw.id = pfw.film_work_id
            JOIN person ON person.id = pfw.person_id
            WHERE person.modified > '{0}'
            GROUP BY pfw.person_id, person.full_name, pfw.role
        """.format(since)
        yield from cls.get_limited_data(query)

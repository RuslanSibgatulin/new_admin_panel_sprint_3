from datetime import datetime
from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import execute_batch, RealDictCursor
from dataclasses import dataclass, field


@dataclass
class PostgresMovies:
    connection: pg_connection
    page_size: int = field(default=5000)

    def save_data(self, table_name, table_fields, data):
        """Загрузка данных data в таблицу table_name и поля table_fields."""

        with self.connection.cursor() as cur:
            fields = ", ".join(table_fields)
            values = ("%s, "*len(table_fields))[:-2]
            query = """INSERT INTO {0} ({1}) VALUES ({2})
            ON CONFLICT (id) DO NOTHING;
            """.format(table_name, fields, values)
            execute_batch(cur, query, data, page_size=self.page_size)
            self.connection.commit()

    def count(self, table_name):
        """Возвращает число строк в таблице."""
        with self.connection.cursor() as cur:
            query = "SELECT COUNT(*) FROM {0}".format(table_name)
            cur.execute(query)
            res = cur.fetchone()
        return res[0]

    def data(self, table_name, table_fields):
        """Возвращает данные таблицы."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            fields = ", ".join(table_fields)
            query = "SELECT {0} FROM {1} ORDER BY id".format(
                fields, table_name
            )
            cur.execute(query)
            res = cur.fetchall()
        return list(map(dict, res))

    def modified_movies(self, since: datetime):

        if not since:
            since = datetime(1, 1, 1)
        query = """
            SELECT
            fw.id, fw.title, fw.description, fw.rating,

            jsonb_object_agg(DISTINCT person.id, person.full_name )
                FILTER (WHERE person_film_work.role = 'actor') AS actors,
            string_agg(DISTINCT person.full_name, ', ')
                FILTER (WHERE person_film_work.role = 'actor') AS actors_names,
            jsonb_object_agg(DISTINCT person.id, person.full_name )
                FILTER (WHERE person_film_work.role = 'writer') AS writers,
            string_agg(DISTINCT person.full_name, ', ')
                FILTER (WHERE person_film_work.role='writer') AS writers_names,
            string_agg(DISTINCT person.full_name, ', ')
                FILTER (WHERE person_film_work.role = 'director') AS director,
            string_agg(DISTINCT genre.name, ', ') AS genre

            FROM film_work as fw
            LEFT OUTER JOIN genre_film_work
                ON (fw.id = genre_film_work.film_work_id)
            LEFT OUTER JOIN genre
                ON (genre_film_work.genre_id = genre.id)
            LEFT OUTER JOIN person_film_work
                ON (fw.id = person_film_work.film_work_id)
            LEFT OUTER JOIN person
                ON (person_film_work.person_id = person.id)

            WHERE fw.modified > '{0}'
            GROUP BY fw.id
            LIMIT 100;
            """.format(since)

        with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            res = cur.fetchall()
        return list(map(dict, res))

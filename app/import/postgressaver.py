from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import execute_batch, RealDictCursor
from dataclasses import dataclass, field


@dataclass
class PostgresSaver:
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

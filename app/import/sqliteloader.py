import sqlite3
from dataclasses import dataclass, field


@dataclass
class SQLiteLoader:
    connection: sqlite3.Connection

    max_rows: int = field(default=1000)

    def loader(self, table_name, table_fields):
        """Загрузчик пакета данных из таблицы БД источника порционно."""
        curs = self.connection.cursor()
        fields = ", ".join(table_fields)
        rows_readed = 0
        while True:
            curs.execute(
                "SELECT {3} FROM {2} LIMIT {0}, {1};"
                .format(rows_readed, self.max_rows, table_name, fields)
            )
            data = curs.fetchall()
            rows_readed += len(data)
            if len(data) == 0:
                break
            else:
                yield data

    def count(self, table_name):
        """Возвращает число строк в таблице."""
        curs = self.connection.cursor()
        curs.execute("SELECT COUNT(*) FROM {0}".format(table_name))
        data = curs.fetchone()
        return data[0]

    def data(self, table_name, table_fields):
        """Возвращает данные таблицы."""

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        fields = ", ".join(table_fields)
        fields = fields.replace("created_at", "created_at as created")
        fields = fields.replace("updated_at", "updated_at as modified")

        self.connection.row_factory = dict_factory
        query = "SELECT {0} FROM {1} ORDER BY id".format(fields, table_name)
        curs = self.connection.cursor()
        curs.execute(query)
        data = curs.fetchall()
        return data

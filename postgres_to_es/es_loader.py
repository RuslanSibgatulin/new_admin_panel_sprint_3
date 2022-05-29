import logging
from elasticsearch7 import Elasticsearch, helpers


class ElasticsearchMovies:

    def __init__(
        self, es_connector: Elasticsearch, index: dict = None
    ) -> None:
        """Создание индекса при инициализации."""

        self.es_conn = es_connector
        if index:
            res = self.create_index('movies', index)
            logging.debug('Create index %s', res)

    def bulk(self, bulk_data: list):
        """Массовая загрузка данных в ES"""
        return helpers.bulk(self.es_conn, bulk_data)

    def exists_index(self, index: str) -> bool:
        """Проверка наличия индекса в ES"""
        return self.es_conn.indices.exists(index=index)

    def create_index(self, index: str, body: dict) -> bool:
        """Создает индекс, если он не существует"""
        if not self.exists_index(index):
            resp = self.es_conn.indices.create(index=index, body=body)
            return resp.get('acknowledged', False)
        else:
            return True

    def online(self) -> bool:
        """Проверка доступности сервера ES."""
        return self.es_conn.ping()

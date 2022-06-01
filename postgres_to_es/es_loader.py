from elasticsearch7 import Elasticsearch, helpers
from backoff import backoff

ES_SCHEMA = {
  "settings": {
    "refresh_interval": "1s",
    "analysis": {
      "filter": {
        "english_stop": {
          "type":       "stop",
          "stopwords":  "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "english_possessive_stemmer": {
          "type": "stemmer",
          "language": "possessive_english"
        },
        "russian_stop": {
          "type":       "stop",
          "stopwords":  "_russian_"
        },
        "russian_stemmer": {
          "type": "stemmer",
          "language": "russian"
        }
      },
      "analyzer": {
        "ru_en": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "english_stop",
            "english_stemmer",
            "english_possessive_stemmer",
            "russian_stop",
            "russian_stemmer"
          ]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "id": {
        "type": "keyword"
      },
      "imdb_rating": {
        "type": "float"
      },
      "genre": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "ru_en",
        "fields": {
          "raw": {
            "type":  "keyword"
          }
        }
      },
      "description": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "director": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "actors_names": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "writers_names": {
        "type": "text",
        "analyzer": "ru_en"
      },
      "actors": {
        "type": "nested",
        "dynamic": "strict",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "analyzer": "ru_en"
          }
        }
      },
      "writers": {
        "type": "nested",
        "dynamic": "strict",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "analyzer": "ru_en"
          }
        }
      }
    }
  }
}


class ElasticsearchMovies:
    """Класс для ETL процесса выгрузки в Elasticsearch."""

    @backoff('ElasticsearchMovies.init', 0.3)
    def __init__(self, es_connector: Elasticsearch):
        """Создание индекса при инициализации."""
        self.es_conn = es_connector
        self.create_index('movies', ES_SCHEMA)

    @backoff('ElasticsearchMovies.bulk', 0.3)
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

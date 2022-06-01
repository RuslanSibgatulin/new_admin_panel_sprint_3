# Запуск приложения
## Подготовить .env файл с переменными окружения
    # Postgres, Django, ETL params
    POSTGRES_USER=
    POSTGRES_PASSWORD=
    POSTGRES_DB=movies_database
    POSTGRES_HOST=postgres

    #Django params
    DEBUG=False
    SECRET_KEY=

    #ETL params
    LIMIT=500
    ETL_INTERVAL=60
    ES_HOST=http://elastic:9200

## Выполнить запуск контейнеров postgres, backend, nginx, elastic
    docker-compose -f "docker-compose.yml" up -d --build postgres backend nginx elastic

## Подготовка БД и учетки админа
Войти в контейнер с именем django_movies и выполнить команду

    python manage.py migrate

Затем создать пользователя (при необходимости использования админки)

    python manage.py createsuperuser

Выгрузить статику

    python manage.py collectstatic

Наполнить БД

    cd import/ && python load_data.py && cat load_data.log

## Запустить ETL контейнер
    docker-compose -f "docker-compose.yml" up -d --build etl
# H1 "API для зберігання та управління контактами"

### H3 docker контейнер для postgres : 
        ʼʼʼ
        docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=123456 -d postgres
        ʼʼʼ

    або

    запуск  docker-compose
        docker compose up -d
        список запущених контейнерів
        docker compose ps 

        docker compose build


### H3 створення міграцій
        alembic init alembic
        alembic revision --autogenerate -m 'Init'
        alembic upgrade head

### H3  наповнення бази фейковими контактами:

        seeds/create_data.py

### H3 запуск 

        uvicorn main:app --host localhost --port 8000 --reload

        або

        fastapi dev main.py


### H3 пошук Query за :
        іменем, 
        прізвищем 
        адресою електронної пошти
        номером телефону

### H3 secret_key - 
        "openssl rand -hex 32"

### H3 очистити кеш
        poetry cache clear --all pypi


### H3 temp maill для тестування
        https://temp-mail.org/uk/

### H3 побудова документації
        sphinx-build -M html docs/source/ docs/build/
        або
        make html
### H3 запуск тестів unittest

        python -m unittest tests/unit_repo_contacts.py 


### H3 запуск pytest

pytest
pytest --cov

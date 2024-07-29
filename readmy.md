1. docker контейнер для postgres : 
docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD
=123456 -d postgres

2. створення міграцій
alembic init alembic
alembic revision --autogenerate -m 'Init'
alembic upgrade head

3. наповнення бази фейковими контактами:

seeds/create_data.py

4. запуск 

uvicorn main:app --host localhost --port 8000 --reload

fastapi dev main.py

5. http://127.0.0.1:8000/api/healthchecker
6. http://127.0.0.1:8000/docs


7. пошук Query за :
        іменем, 
        прізвищем 
        адресою електронної пошти
        номером телефону

8. secret_key "openssl rand -hex 32"

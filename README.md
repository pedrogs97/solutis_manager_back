Comando para migrations dentro do Docker: 
 - docker-compose run --user 1000 [app-service] sh -c 'alembic revision --autogenerate -m "[migration name]"'\
Comando para migrations:
 - alembic revision --autogenerate -m "[migration name]"

Comando para aplicar migration dentro do Docker:
 - docker-compose run --user 1000 [app-service] sh -c 'alembic upgrade head'
Comando para aplicar migrations:
 - alembic upgrade head
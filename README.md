Comando para migrations dentro do Docker:
 - docker-compose run --user 1000 [app-service] sh -c 'alembic revision --autogenerate -m "[migration name]"'\
Comando para migrations:
 - alembic revision --autogenerate -m "[migration name]"

Comando para aplicar migration dentro do Docker:
 - docker-compose run --user 1000 [app-service] sh -c 'alembic upgrade head'
Comando para aplicar migrations:
 - alembic upgrade head

Comando para limpar layers do docker:
 - docker system prune -a -f

Comando para limpar os containers:
 - docker rm -v $(docker ps -a -q -f status=exited)

Comando para limpar os volumes:
 - docker volume ls -qf dangling=true | xargs -r docker volume rm

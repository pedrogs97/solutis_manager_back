#!/bin/bash

# Função para verificar se um comando foi executado com sucesso
check_command() {
    if [ $? -ne 0 ]; then
        echo "Erro ao executar: $1"
    else
        echo "Comando executado com sucesso: $1"
    fi
}

echo "Parando os serviços Docker Compose..."
docker compose stop
check_command "docker compose stop"

echo "Removendo containers..."
docker compose rm -f
check_command "docker compose rm -f"

echo "Removendo volumes não utilizados..."
docker volume ls -qf dangling=true | xargs -r docker volume rm
check_command "docker volume ls -qf dangling=true | xargs -r docker volume rm"

echo "Limpando o sistema Docker..."
docker system prune -a -f
check_command "docker system prune -a -f"

echo "Reconstruindo e iniciando os serviços em segundo plano..."
docker compose up --build -d
check_command "docker compose up --build -d"

echo "Script concluído."

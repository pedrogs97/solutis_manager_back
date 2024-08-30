#!/bin/bash

# Função para verificar se um comando foi executado com sucesso
check_command() {
    if [ $? -ne 0 ]; then
        echo "Erro ao executar: $1"
    else
        echo "Comando executado com sucesso: $1"
    fi
}

echo "Executando migrations..."
docker compose exec agile inv migrate

echo "Script concluído."

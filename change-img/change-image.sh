#!/bin/bash

# Caminho para o diretório contendo as fotos
caminho_fotos="./change-img/input"

# Caminho para o diretório de destino
caminho_destino="./change-img/output"

# Verifica se o diretório das fotos existe
if [ ! -d "$caminho_fotos" ]; then
    echo "Erro: O diretório '$caminho_fotos' não existe."
    exit 1
fi

# Verifica se o diretório de destino existe
if [ ! -d "$caminho_destino" ]; then
    echo "Erro: O diretório '$caminho_destino' não existe."
    exit 1
fi

# Lista todas as fotos no diretório
fotos=("$caminho_fotos"/*)

# Verifica se existem fotos no diretório
if [ ${#fotos[@]} -eq 0 ]; then
    echo "Erro: Não há fotos no diretório '$caminho_fotos'."
    exit 1
fi

# Seleciona uma foto aleatória
foto_aleatoria=${fotos[RANDOM % ${#fotos[@]}]}

# Nome da foto após renomear
novo_nome="nova_foto.jpg"

# Move a foto selecionada para o diretório de destino com o novo nome
cp "$foto_aleatoria" "$caminho_destino/$novo_nome"

echo "Foto '$foto_aleatoria' movida para '$caminho_destino/$novo_nome'."

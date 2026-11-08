#!/usr/bin/env bash
# Script automatizado para deploy no PythonAnywhere
set -e

echo "🚀 Iniciando configuração no PythonAnywhere..."

if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
fi

echo "📦 Instalando dependências..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "🎨 Coletando arquivos estáticos..."
.venv/bin/python manage.py collectstatic --noinput

echo "🗄️ Aplicando migrações no banco de dados..."
.venv/bin/python manage.py migrate

echo "✨ Inicializando dados do evento MDX 2026..."
.venv/bin/python manage.py setup_event

echo "🎉 Pronto! Agora configure as rotas estáticas na aba 'Web' e clique em Reload!"


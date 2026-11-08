#!/usr/bin/env bash
# Script de build para deploy gratuito no Render / Koyeb
set -o errexit

echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🗄️ Executando migrações do banco de dados..."
python manage.py migrate

echo "✨ Inicializando desafio da Rodada 01 e operador do estande..."
python manage.py setup_event

echo "🎉 Build concluído com sucesso para o MDX 2026!"


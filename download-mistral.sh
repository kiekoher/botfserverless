#!/bin/bash
set -e

mkdir -p ~/dueloanimalbot/models
cd ~/dueloanimalbot/models

echo "⬇️ Descargando modelo Mistral 3B Instruct (Q4_K_M)..."
wget -c https://huggingface.co/TheBloke/Mistral-3B-Instruct-v0.1-GGUF/resolve/main/mistral-3b-instruct-v0.1.Q4_K_M.gguf

echo "✅ Modelo descargado correctamente."

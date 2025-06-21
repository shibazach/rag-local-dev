#!/bin/bash
set -e

echo "🧠 Pulling models..."
ollama pull "${OLLAMA_MODEL}" || exit 1
ollama pull nomic-embed-text || exit 1

echo "⏳ Waiting 5 seconds before starting Ollama..."
sleep 5

echo "🚀 Starting Ollama..."
exec ollama serve

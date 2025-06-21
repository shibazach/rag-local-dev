#!/bin/bash
# REM: Ollama 本体 + 必要モデルをインストール & 自動起動するセットアップ

set -e

echo "🧠 Step 1: Installing Ollama (if not installed)..."
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "✅ Ollama already installed."
fi

echo "📦 Step 2: Pulling required models..."
ollama pull phi4-mini || true
ollama pull nomic-embed-text || true

echo "🚀 Step 3: Starting Ollama service in background..."
# 既に起動していなければ serve
pgrep -f "ollama serve" >/dev/null || nohup ollama serve > ~/ollama.log 2>&1 &

echo "✅ Ollama is running at http://localhost:11434"

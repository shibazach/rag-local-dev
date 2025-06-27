#!/usr/bin/env bash
# ------------------------------------------------------------
# REM: CPU/GPU 用の devcontainer/Dockerfile/docker-compose ファイルを切り替えるスクリプト
# REM: 実行はプロジェクトルートで行い、以下のファイルをコピー
#       - devcontainer.cpu.jsonc → devcontainer.json
#       - devcontainer.gpu.jsonc → devcontainer.json
#       - Dockerfile.cpu       → Dockerfile
#       - Dockerfile.gpu       → Dockerfile
#       - docker-compose.cpu.yml → docker-compose.yml
#       - docker-compose.gpu.yml → docker-compose.yml
# ------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ファイル名定義
DEV_CPU="${SCRIPT_DIR}/.devcontainer/devcontainer.cpu.jsonc"
DEV_GPU="${SCRIPT_DIR}/.devcontainer/devcontainer.gpu.jsonc"
DOCKERFILE_CPU="${SCRIPT_DIR}/.devcontainer/Dockerfile.cpu"
DOCKERFILE_GPU="${SCRIPT_DIR}/.devcontainer/Dockerfile.gpu"
COMPOSE_CPU="${SCRIPT_DIR}/docker-compose.cpu.yml"
COMPOSE_GPU="${SCRIPT_DIR}/docker-compose.gpu.yml"

DEST_DEV="${SCRIPT_DIR}/.devcontainer/devcontainer.json"
DEST_DF="${SCRIPT_DIR}/.devcontainer/Dockerfile"
DEST_COMPOSE="${SCRIPT_DIR}/docker-compose.yml"

# 存在チェック関数
check_exists() {
  [[ -f "$1" ]] || { echo "❌ ファイルが見つかりません: $1"; exit 1; }
}

check_exists "$DEV_CPU"
check_exists "$DEV_GPU"
check_exists "$DOCKERFILE_CPU"
check_exists "$DOCKERFILE_GPU"
check_exists "$COMPOSE_CPU"
check_exists "$COMPOSE_GPU"

echo "============================================"
echo "  CPU/GPU 環境切替スクリプト"
echo "============================================"
echo "1) GPU 用に切り替え"
echo "2) CPU 用に切り替え"
read -rp "番号を選んで Enter ▶ " CHOICE

case "$CHOICE" in
  1)
    echo "🔄 GPU 用ファイルを適用中..."
    cp "$DEV_GPU" "$DEST_DEV"
    cp "$DOCKERFILE_GPU" "$DEST_DF"
    cp "$COMPOSE_GPU" "$DEST_COMPOSE"
    MODE="GPU"
    ;;
  2)
    echo "🔄 CPU 用ファイルを適用中..."
    cp "$DEV_CPU" "$DEST_DEV"
    cp "$DOCKERFILE_CPU" "$DEST_DF"
    cp "$COMPOSE_CPU" "$DEST_COMPOSE"
    MODE="CPU"
    ;;
  *)
    echo "❌ 1 または 2 を入力してください"
    exit 1
    ;;
esac

echo "✅ 完了: ${MODE} モードに切り替えました"
echo "   次に: docker compose down && docker compose up -d --build を実行してください"

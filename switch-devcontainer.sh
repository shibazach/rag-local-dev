#!/usr/bin/env bash
# ------------------------------------------------------------
# REM: GPU / CPU 用 devcontainer ファイルをワンコマンドで切替
#      - リポジトリ直下で実行
#      - .devcontainer 内に
#          * devcontainer.{gpu,cpu}.jsonc   ←★ jsonc 版
#      がある前提
# ------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DC_DIR="${SCRIPT_DIR}/.devcontainer"

if [[ ! -d "$DC_DIR" ]]; then
  echo "❌  .devcontainer ディレクトリが見つかりません: $DC_DIR"
  exit 1
fi

echo "==============================="
echo "  devcontainer 環境切り替え"
echo "==============================="
echo "1) GPU  (nvidia/cuda + --gpus all)"
echo "2) CPU  (NVIDIA_DISABLE_REQUIRE=1)"
read -rp "番号を選んで Enter ▶ " ANSWER

case "$ANSWER" in
  1) SRC_JSON="devcontainer.gpu.jsonc" ; NOTE="GPU" ;;
  2) SRC_JSON="devcontainer.cpu.jsonc" ; NOTE="CPU" ;;
  *) echo "❌ 1 か 2 を入力してください" ; exit 1 ;;
esac

echo "🔄  $NOTE 用 devcontainer に切り替え中..."
cp  "${DC_DIR}/${SRC_JSON}"  "${DC_DIR}/devcontainer.json"

echo "✅  完了しました → .devcontainer/devcontainer.json を更新"
echo "   VS Code で『Reopen in Container』を実行してください。"

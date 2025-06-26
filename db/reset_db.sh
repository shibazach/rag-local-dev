#!/bin/bash

cd "$(dirname "$0")"

echo "⚠️ この操作は PostgreSQL のデータ（volume）を完全に削除します。"
echo "   対象ボリューム: db_pgdata"
echo "   対象コンテナ : pgvector-db"
echo ""

read -p "本当に初期化しますか？ [yes/NO]: " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "❎ キャンセルされました。変更はありません。"
  exit 0
fi

echo "🛑 コンテナ停止・削除"
docker compose down

echo "🧹 volume 削除（データ全消去）"
docker volume rm db_pgdata

echo "🧼 ネットワークも削除（必要に応じて）"
docker network rm db_ragnet 2>/dev/null || echo "⚠️ ネットワークは存在しないか、他のサービスで使用中"

echo "♻️ 完全リセット完了！再構築には ./setup_db.sh を実行してください。"

#!/bin/bash

# ユーザー辞書CSVと出力先
CSV_PATH="./user_dict.csv"
DIC_PATH="./custom.dic"
IPADIC_PATH="/var/lib/mecab/dic/ipadic-utf8"

# CSVの存在チェック
if [ ! -f "$CSV_PATH" ]; then
  echo "❌ CSVファイルが見つかりません: $CSV_PATH"
  exit 1
fi

# MeCab辞書ビルドコマンド
echo "🔧 ユーザー辞書をビルド中..."
/usr/lib/mecab/mecab-dict-index -d "$IPADIC_PATH" -u "$DIC_PATH" -f utf-8 -t utf-8 "$CSV_PATH"

# 結果チェック
if [ $? -eq 0 ]; then
  echo "✅ 辞書ビルド成功: $DIC_PATH を生成しました"
else
  echo "❌ 辞書ビルドに失敗しました"
  exit 1
fi

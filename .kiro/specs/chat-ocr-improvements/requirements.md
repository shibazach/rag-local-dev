# Requirements Document

## Introduction

このspecは、RAGシステムにおける2つの重要な改善を実装します：
1. チャット機能のプロンプト管理を外部ファイル化し、保守性を向上させる
2. OCR設定ダイアログ機能を復旧・改善し、ingestとtry_ocrページで統一的に使用できるようにする

これらの改善により、システムの保守性、拡張性、ユーザビリティが大幅に向上します。

## Requirements

### Requirement 1: チャットプロンプトの外部ファイル化

**User Story:** システム管理者として、チャット機能のプロンプトを外部ファイルで管理したい。これにより、コードを変更せずにプロンプトの調整や多言語対応が可能になる。

#### Acceptance Criteria

1. WHEN チャットハンドラーがプロンプトを必要とする THEN 外部ファイルからセクション化されたプロンプトを読み込む SHALL システム
2. WHEN プロンプトファイルに複数のセクションが定義されている THEN `<section_name></section_name>`タグで区切られたセクションを正確に抽出する SHALL システム
3. WHEN 「チャンク統合」モードが選択されている THEN 専用のプロンプトセクションを使用する SHALL システム
4. WHEN 「ファイル別」モードが選択されている THEN 要約・評価用の専用プロンプトセクションを使用する SHALL システム
5. WHEN llm/prompt_loader.pyが呼び出される THEN ingestとchat両方のプロンプト読み込みに対応する SHALL システム

### Requirement 2: OCR設定ダイアログの復旧・統一化

**User Story:** ユーザーとして、ingestページとtry_ocrページの両方で同じOCR設定ダイアログを使用したい。これにより、一貫した操作性でOCRエンジンの詳細設定が可能になる。

#### Acceptance Criteria

1. WHEN ingestページの「設定」ボタンがクリックされる THEN OCRエンジン設定ダイアログが表示される SHALL システム
2. WHEN try_ocrページの「エンジン調整」がクリックされる THEN 同じOCR設定ダイアログが表示される SHALL システム
3. WHEN OCR設定ダイアログが表示される THEN エンジン名、「閉じる」ボタン、「保存」ボタンが上部に配置される SHALL システム
4. WHEN 設定項目が表示される THEN 項目名（太字・左揃え）、コントロール（位置揃え）、説明（薄字・小さめ）が一列に表示される SHALL システム
5. WHEN 各OCRエンジンが選択される THEN そのエンジンの精度に影響する全ての設定項目が表示される SHALL システム
6. WHEN 設定が保存される THEN ingestとtry_ocr両方で同じ設定が適用される SHALL システム

### Requirement 3: プロンプト管理の統一化

**User Story:** 開発者として、ingestとchatのプロンプト管理を統一したい。これにより、コードの重複を削減し、保守性を向上させる。

#### Acceptance Criteria

1. WHEN llm/prompt_loader.pyが拡張される THEN ingestとchat両方のプロンプト読み込みに対応する SHALL システム
2. WHEN プロンプトファイルが読み込まれる THEN セクションタグによる柔軟な区切りに対応する SHALL システム
3. WHEN llm/refiner.pyが更新される THEN chat機能でも流用可能な構造になる SHALL システム
4. WHEN 新しいプロンプトタイプが追加される THEN 既存のコードに影響を与えずに拡張可能である SHALL システム

### Requirement 4: OCR設定の共通化

**User Story:** 開発者として、OCR設定ダイアログの機能を別ファイルに切り出したい。これにより、複数のページから同じ機能を呼び出せるようになる。

#### Acceptance Criteria

1. WHEN OCR設定ダイアログが別ファイルに切り出される THEN ingestとtry_ocrの両方から呼び出し可能である SHALL システム
2. WHEN OCR設定が変更される THEN リアルタイムでプレビューが更新される SHALL システム
3. WHEN 設定項目が表示される THEN 行間を最小限に抑えた密な表示になる SHALL システム
4. WHEN プリセット機能が実装される THEN 設定の保存・読み込み・削除が可能である SHALL システム
5. WHEN エンジンが切り替えられる THEN そのエンジン固有の設定項目のみが表示される SHALL システム
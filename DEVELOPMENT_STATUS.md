# 開発進捗

> **最終更新**: 2025-12-20

## 開発フェーズ

| フェーズ | 対応データソース | ステータス |
| ------- | --------------- | --------- |
| **Phase 1** | ローカルフォルダ監視 | ✅ 完了 |
| **Phase 2** | Dropbox / OneDrive / SharePoint | 📋 計画中 |

## セットアップ進捗

### 完了したステップ

| Step | 内容 | 状態 | 備考 |
| ---- | ---- | ---- | ---- |
| 1 | Docker環境構築 | ✅ 完了 | 全11コンテナ起動確認済み |
| 2 | Difyセットアップ | ✅ 完了 | 管理者アカウント作成済み |
| 3 | Geminiモデルプロバイダー設定 | ✅ 完了 | APIキー設定済み |
| 4 | ナレッジベース作成 | ✅ 完了 | `DocuSearch` 作成済み（ID: `b548ea8c-...`） |
| 5 | アプリ作成・API Key取得 | ✅ 完了 | チャットボット`DocuSearch`作成、APIキー発行済み |
| 6 | n8n設定 | ✅ 完了 | ワークフローインポート済み、クレデンシャル設定完了 |
| 7 | ドキュメント処理テスト | ✅ 完了 | `TEST - Document Processing` 成功 |
| 8 | 画像処理テスト | ✅ 完了 | `TEST - Image Processing` 成功（Gemini Vision連携確認） |
| 9 | Local Folder Monitor動作確認 | ✅ 完了 | サブワークフロー呼び出し成功 |

## n8nワークフロー一覧

| ワークフロー | 用途 | 公開状態 |
| ------------ | ---- | -------- |
| Document Processing - DocuSearch | ドキュメントのDify登録 | ✅ 公開済み |
| Image Processing - DocuSearch | 画像のEXIF抽出・Vision分析・Dify登録 | ✅ 公開済み |
| Local Folder Monitor - DocuSearch | フォルダ監視・自動処理呼び出し | ✅ 公開済み |

## 起動中のコンテナ

```text
docusearch-postgres      ✅ healthy
docusearch-redis         ✅ healthy
docusearch-weaviate      ✅ healthy
docusearch-sandbox       ✅ running
docusearch-ssrf-proxy    ✅ running
docusearch-plugin-daemon ✅ running
docusearch-dify-api      ✅ running
docusearch-dify-worker   ✅ running
docusearch-dify-web      ✅ running
docusearch-n8n           ✅ running
docusearch-nginx         ✅ running
```

---

## 宿題・TODO

### 優先度: 高

- [x] **EXIF抽出の本格実装** ✅ 完了
  - JavaScriptでJPEG EXIF解析を実装
  - GPS座標（緯度・経度）を正しく抽出
  - 撮影日時、カメラ情報も取得

- [ ] **ファイル削除同期機能の動作確認**
  - `watch/`フォルダからファイル削除時、Difyからも自動削除
  - `DIFY_DATASET_ID`環境変数を`.env`に設定が必要
  - n8nでLocal Folder Monitorワークフローを再インポート

- [ ] **n8n環境変数でワークフローID参照を確認**
  - 現在はワークフローIDを直接ハードコード
  - 確認後、`$env.IMAGE_PROCESSING_WORKFLOW_ID` 形式に変更可能

### 優先度: 中

- [ ] **ジオコーディングの統合テスト**
  - GPS座標から住所への変換が正しく動作するか確認
  - Nominatim APIのレート制限に注意

- [ ] **検索精度の確認**
  - 登録したデータが意図通りに検索できるかテスト
  - Gemini Visionのキャプション品質を確認

### 優先度: 低

- [ ] **Phase 2: クラウドストレージ連携**
  - Dropbox連携
  - OneDrive連携
  - SharePoint連携

- [ ] **本番環境向けセキュリティ設定**
  - Weaviate認証の有効化
  - HTTPS対応
  - ファイアウォール設定

---

## 解決した問題

| 問題 | 原因 | 解決策 |
| ---- | ---- | ------ |
| n8nファイルアクセスエラー | `N8N_RESTRICT_FILE_ACCESS_TO` 制限 | 空文字で無効化 |
| Dify API認証エラー | アプリ未作成でAPIキーなし | チャットボット作成が必要 |
| n8nクレデンシャル消失 | コンテナ再作成で初期化 | 再設定が必要 |
| Weaviateインデックスエラー | `WEAVIATE_API_KEY` 未設定 | 空文字を明示的に設定 |
| Gemini Vision Base64エラー | n8nで`binaryData.data`が参照文字列を返す | `this.helpers.getBinaryDataBuffer()`を使用 |
| n8n child_processエラー | Codeノードで`require('child_process')`が禁止 | Execute Commandノードに変更 |
| サブワークフロー呼び出しエラー | 名前参照が動作しない | ID参照（`mode: "id"`）に変更 |
| Base64エンコードエラー | `readWriteFile`が参照文字列のみ渡す | 子ワークフローで`readBinaryFile`を使用 |

---

## 技術メモ

### APIキーの種類

| キー種別 | 形式 | 用途 |
| -------- | ---- | ---- |
| App API Key | `app-xxxxx` | チャットボットアプリのAPI呼び出し |
| Dataset API Key | `dataset-xxxxx` | n8nからDify Knowledge Base APIへのアクセス |

### n8nクレデンシャル設定

n8nの「Dataset API Key」クレデンシャルには**Dataset API Key**（`dataset-`で始まるキー）を使用:

- **Credential Type**: Header Auth
- **Name**: `Authorization`
- **Value**: `Bearer dataset-xxxxxxxx`

Dataset API Keyは Dify「ナレッジ」→「API ACCESS」タブから発行できます。

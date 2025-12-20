# トラブルシューティング

このドキュメントでは、よくある問題とその解決方法を記載します。

## 解決済みの問題一覧

| 問題 | 原因 | 解決策 |
| ---- | ---- | ------ |
| n8nファイルアクセスエラー | `N8N_RESTRICT_FILE_ACCESS_TO` 制限 | 空文字で無効化 |
| Dify API認証エラー | アプリ未作成でAPIキーなし | チャットボット作成が必要 |
| n8nクレデンシャル消失 | コンテナ再作成で初期化 | 再設定が必要 |
| Weaviateインデックスエラー | `WEAVIATE_API_KEY` 未設定 | 空文字を明示的に設定 |
| Gemini Vision Base64エラー | n8nで`binaryData.data`が参照文字列を返す | `this.helpers.getBinaryDataBuffer()`を使用 |
| n8n child_processエラー | Codeノードで`require('child_process')`が禁止 | Execute Commandノードに変更 |

---

## Dify関連

### 「Internal Server Error」が表示される

初回起動時にデータベーステーブルが作成されていない場合に発生します。

```bash
# データベースマイグレーションを実行
docker compose exec dify-api flask db upgrade

# サービスを再起動
docker compose restart dify-api dify-worker
```

### Difyにアクセスできない

```bash
# Difyサービスの状態確認
docker compose ps dify-api dify-web

# 依存サービスが起動しているか確認
docker compose ps postgres redis weaviate
```

### ナレッジベースにドキュメントが登録されない

1. n8nの実行履歴を確認
2. Dify APIのレスポンスを確認
3. Dataset API Keyが正しく設定されているか確認

---

## n8n関連

### 「Module 'child_process' is disallowed」エラー

Local Folder Monitorで発生する場合、古いバージョンのJSONファイルを使用しています。
最新の `local-folder-monitor.json` を再インポートしてください。

### 「Unsupported MIME type」エラー

Image Processingで発生する場合、バイナリデータが正しく渡されていません。

1. ワークフローを削除
2. 最新の `image-processing.json` を再インポート
3. 再度公開

### サブワークフローが呼び出せない / 「Workflow does not exist」

- サブワークフロー（Document Processing, Image Processing）が**公開済み**であることを確認
- ワークフローIDが正しいことを確認
- 名前ではなくID参照を使用（`mode: "id"`）

### 「Base64 decoding failed for 'filesystem-v2'」エラー

**原因**: 親ワークフローから子ワークフローへバイナリデータを渡す際、`readWriteFile`ノードは参照文字列のみを渡すため発生します。

**解決策**: Image Processingワークフローがファイルパスのみを受け取り、自身で`readBinaryFile`ノードを使ってファイルを読み込む設計にします。

### 「access to env vars denied」エラー

n8nは環境変数へのアクセスをデフォルトで制限しています。

**解決策**:

1. ワークフローIDを直接JSONに記載（推奨）
2. または、n8nの Variables 機能を使用

### クレデンシャルが消える

コンテナを再作成すると、n8nのデータが初期化される場合があります。

**予防策**: `volumes/n8n_data` が正しくマウントされていることを確認

```yaml
volumes:
  - ./volumes/n8n_data:/home/node/.n8n
```

---

## Docker関連

### サービスが起動しない

```bash
# ログを確認
docker compose logs postgres
docker compose logs dify-api

# サービスを再起動
docker compose restart
```

### メモリ不足

Docker Desktopの設定でメモリを増やしてください（8GB以上推奨）

### ポートが使用中

`.env` または `docker-compose.yml` でポート番号を変更

---

## Gemini API関連

### 「API key not valid」エラー

1. Gemini API Keyが正しいか確認
2. [Google AI Studio](https://aistudio.google.com/) でキーが有効か確認
3. `.env` ファイルの `GEMINI_API_KEY` を確認

### Vision APIのレート制限

Gemini APIには利用制限があります。短時間に大量の画像を処理すると制限に達する場合があります。

**対策**: n8nワークフローで処理間隔を設定

---

## 本番環境向けセキュリティ設定

> **Note**: 現在の設定はローカル開発環境向けです。本番環境へデプロイする際は以下のセキュリティ設定を検討してください。

### Weaviate認証の有効化

現在、Weaviateは匿名アクセスを許可しています（`AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'`）。本番環境では認証を有効にすることを推奨します。

#### 1. Weaviateの設定変更

```yaml
# docker-compose.yml - weaviate サービス
weaviate:
  environment:
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
    AUTHENTICATION_APIKEY_ENABLED: 'true'
    AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'your-secure-weaviate-api-key'
    AUTHENTICATION_APIKEY_USERS: 'dify'
```

#### 2. Difyの設定変更

```yaml
# docker-compose.yml - dify-api, dify-worker サービス
environment:
  WEAVIATE_API_KEY: 'your-secure-weaviate-api-key'
```

### その他の推奨設定

| 項目 | 開発環境 | 本番環境 |
| ---- | ------- | ------- |
| Weaviate認証 | 匿名アクセス許可 | APIキー必須 |
| Redis パスワード | 簡易パスワード | 強力なパスワード |
| PostgreSQL | ローカルアクセスのみ | SSL接続 + 強力なパスワード |
| HTTPS | 不要 | 必須（Let's Encrypt等） |
| ファイアウォール | 全ポート開放 | 必要最小限のポートのみ |

---

## 次のステップ

- [環境構築手順](./SETUP.md)
- [n8nワークフロー設定](./N8N_WORKFLOW_SETUP.md)
- [アーキテクチャ解説](./ARCHITECTURE.md)

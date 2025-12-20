# DocuSearch_AI

非構造化データ（ドキュメント・画像）を構造化し、自然言語で検索可能にするRAG（Retrieval-Augmented Generation）プラットフォーム

## 機能

- **画像の自動解析**: EXIF情報（撮影日時・GPS座標）を抽出し、Vision AIで画像内容をテキスト化
- **ドキュメントのインデックス化**: PDF、Word、Excelなどを自動でチャンク分割・ベクトル化
- **セマンティック検索**: 「去年の東京での会議資料」「マンションの外観写真」など自然言語で検索
- **複数データソース対応**: ローカルフォルダを監視して自動処理（Phase 2でクラウドストレージ対応予定）

## クイックスタート

### 1. 環境設定

```bash
cp .env.example .env
# .envを編集してパスワードとAPIキーを設定
```

### 2. サービス起動

```bash
docker compose up -d
```

### 3. 初期設定

1. <http://localhost> にアクセスしてDifyの管理者アカウントを作成
2. <http://localhost:5678> でn8nのワークフローを設定

詳細は [docs/SETUP.md](docs/SETUP.md) を参照してください。

## サービス一覧

| サービス | ポート | 説明 |
| -------- | ------ | ---- |
| Dify Web | 3000 | RAGプラットフォームUI |
| Dify API | 5001 | REST API |
| n8n | 5678 | ワークフロー自動化 |
| Weaviate | 8080 | ベクトルデータベース |
| PostgreSQL | 5432 | メタデータDB |
| Redis | 6379 | キャッシュ |
| Nginx | 80 | リバースプロキシ（統合エントリポイント） |

## ディレクトリ構造

```text
DocuSearch_AI/
├── docker-compose.yml      # サービス定義
├── .env.example            # 環境変数テンプレート
├── nginx/
│   └── nginx.conf          # リバースプロキシ設定
├── n8n/
│   └── workflows/          # n8nワークフローJSON
├── scripts/                # Pythonユーティリティ
├── watch/                  # 監視フォルダ
│   ├── documents/          # ドキュメント投入
│   └── images/             # 画像投入
├── volumes/                # 永続化データ
└── docs/                   # ドキュメント
```

## ドキュメント

| ドキュメント | 内容 |
| ------------ | ---- |
| [docs/SETUP.md](docs/SETUP.md) | 環境構築手順 |
| [docs/N8N_WORKFLOW_SETUP.md](docs/N8N_WORKFLOW_SETUP.md) | n8nワークフロー詳細設定 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | システムアーキテクチャ解説 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | トラブルシューティング |
| [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) | 開発進捗・TODO |

## 必要条件

- Docker Desktop
- Gemini API Key（画像解析用）
- 8GB以上のRAM推奨

## Pythonスクリプト

`scripts/` フォルダにはテスト・デバッグ用のPythonスクリプトがあります。

```bash
cd scripts
pip install -r requirements.txt

# EXIF情報抽出
python exif_extractor.py /path/to/image.jpg

# GPS座標を住所に変換
python geocoder.py 35.6895 139.6917

# 画像処理（統合）
python image_processor.py /path/to/image.jpg
```

## 開発フェーズ

| フェーズ | 対応データソース | ステータス |
| ------- | --------------- | --------- |
| **Phase 1** | ローカルフォルダ監視 | ✅ 完了 |
| **Phase 2** | Dropbox / OneDrive / SharePoint | 📋 計画中 |

## ライセンス

MIT License

## 参考リンク

- [Dify ドキュメント](https://docs.dify.ai/)
- [n8n ドキュメント](https://docs.n8n.io/)
- [Weaviate ドキュメント](https://weaviate.io/developers/weaviate)
- [Gemini API ドキュメント](https://ai.google.dev/docs)

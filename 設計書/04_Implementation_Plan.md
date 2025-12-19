# DocuSearch_AI 実装計画

## 概要

設計書に基づき、RAG（Retrieval-Augmented Generation）プラットフォームを構築する。

- **デプロイパターン:** Pattern C（ライトウェイト・ハイブリッド）
- **Vision API:** Gemini 2.5 Flash

## 開発フェーズ

| フェーズ | スコープ | ステータス |
|---------|---------|-----------|
| **Phase 1** | ローカルフォルダ監視 | 🚧 開発中 |
| **Phase 2** | クラウドストレージ連携（Dropbox/OneDrive/SharePoint） | 📋 計画中 |

---

## Phase 1: ローカルフォルダ監視

### 対象機能

- ローカルフォルダ（`watch/images`, `watch/documents`）の監視
- 画像処理パイプライン（EXIF抽出 → ジオコーディング → Vision AI → Dify登録）
- ドキュメント処理パイプライン（Difyアップロード → インデックス化）
- 5分間隔の差分検出・処理

### プロジェクト構造

```
DocuSearch_AI/
├── docker-compose.yml          # メインオーケストレーション
├── .env.example                # 環境変数テンプレート
├── nginx/
│   └── nginx.conf              # リバースプロキシ設定
├── scripts/                    # Pythonユーティリティ
│   ├── requirements.txt
│   ├── exif_extractor.py       # EXIF抽出
│   ├── geocoder.py             # GPS→住所変換
│   └── image_processor.py      # 画像処理統合
├── n8n/
│   └── workflows/              # ワークフロー定義
├── volumes/                    # 永続化データ
└── watch/                      # ローカル監視フォルダ
    ├── documents/
    └── images/
```

### 実装ステップ

#### Step 1: インフラ構築

1. `docker-compose.yml` 作成
   - PostgreSQL (Dify + n8n共用)
   - Redis
   - Weaviate (ベクトルDB)
   - Dify (api, worker, web, sandbox)
   - n8n
   - Nginx

2. `.env.example` 作成（API キー、DB認証情報）

3. `nginx/nginx.conf` 作成（リバースプロキシ）

4. `init-db.sql` 作成（DB初期化）

5. ディレクトリ構造作成

#### Step 2: Pythonスクリプト

1. `scripts/requirements.txt`
   - Pillow, requests, piexif

2. `scripts/exif_extractor.py`
   - 画像からEXIF抽出（日時、GPS座標）
   - DMS→10進数変換

3. `scripts/geocoder.py`
   - Nominatim対応（無料）
   - GPS座標→住所変換

4. `scripts/image_processor.py`
   - EXIF抽出 + ジオコーディング統合
   - Difyインデックス用テキスト生成

#### Step 3: n8nワークフロー構築

1. **ローカルフォルダ監視ワークフロー**
   - Schedule Trigger (5分間隔)
   - ファイル読み込み → 種類判定 → 処理振り分け
   - 処理済みファイルの管理

2. **画像処理サブワークフロー**
   - EXIF抽出 (Code Node)
   - ジオコーディング (HTTP Request)
   - Gemini Vision API (HTTP Request)
   - Dify Knowledge API (HTTP Request)

3. **ドキュメント処理サブワークフロー**
   - Difyファイルアップロード

#### Step 4: 統合テスト

1. サンプルファイルでE2Eテスト
2. Difyナレッジベース検索確認
3. パラメータチューニング

### 必要な外部サービス・APIキー（Phase 1）

| サービス | 必須/任意 | 用途 |
|---------|----------|------|
| **Gemini API Key** | 必須 | 画像解析 |
| **Google Maps API Key** | 任意 | 高精度ジオコーディング（Nominatimで代替可） |

---

## Phase 2: クラウドストレージ連携（計画中）

### 対象機能

- Dropbox連携
- OneDrive連携
- SharePoint連携
- Google Drive連携（検討中）

### 追加ワークフロー

1. **Dropbox同期ワークフロー**
   - Dropbox API連携（OAuth2）
   - デルタ同期（カーソル管理）

2. **OneDrive同期ワークフロー**
   - Microsoft Graph API連携

3. **SharePoint同期ワークフロー**
   - Microsoft Graph API連携

### 追加で必要なAPIキー（Phase 2）

| サービス | 用途 |
|---------|------|
| **Dropbox App** | OAuth2認証 |
| **Azure AD App** | OneDrive/SharePoint認証 |
| **Google Cloud OAuth** | Google Drive認証 |

---

## 主要API仕様

### Gemini Vision API
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
Header: x-goog-api-key: {GEMINI_API_KEY}
```

### Dify Knowledge API
```
POST /v1/datasets/{dataset_id}/document/create-by-text
Header: Authorization: Bearer {DIFY_KNOWLEDGE_API_KEY}
```

### Nominatim Geocoding
```
GET https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=ja
```

---

## 作成ファイル一覧（Phase 1）

| ファイル | 目的 | ステータス |
|---------|------|-----------|
| `docker-compose.yml` | 全サービス定義 | ✅ 完了 |
| `.env.example` | 環境変数テンプレート | ✅ 完了 |
| `nginx/nginx.conf` | リバースプロキシ | ✅ 完了 |
| `init-db.sql` | DB初期化SQL | ✅ 完了 |
| `scripts/requirements.txt` | Python依存関係 | ✅ 完了 |
| `scripts/exif_extractor.py` | EXIF抽出 | ✅ 完了 |
| `scripts/geocoder.py` | ジオコーディング | ✅ 完了 |
| `scripts/image_processor.py` | 画像処理統合 | ✅ 完了 |
| `n8n/workflows/*.json` | ワークフロー定義 | ✅ 完了 |

---

## Dify検索設定（推奨値）

- Top K: 5
- Score Threshold: 0.5
- Rerank: 有効
- チャンク: 500-1000トークン

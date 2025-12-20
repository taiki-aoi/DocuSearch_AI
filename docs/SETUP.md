# 環境構築手順

このドキュメントでは、DocuSearch_AIの環境構築手順を説明します。

## 必要条件

- Docker Desktop
- Gemini API Key（画像解析用）
- 8GB以上のRAM推奨

## 1. 環境設定

```bash
# リポジトリをクローン（または展開）
cd DocuSearch_AI

# 環境変数ファイルを作成
cp .env.example .env
```

`.env` ファイルを編集して、以下の値を設定：

```bash
# 必須: パスワードを安全な値に変更
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
DIFY_SECRET_KEY=your_32_character_secret_key_here
N8N_ENCRYPTION_KEY=your_24_character_key_here

# 必須: Gemini API Key
# https://aistudio.google.com/ で取得
GEMINI_API_KEY=your_gemini_api_key
```

## 2. サービス起動

```bash
# 全サービスを起動
docker compose up -d

# 起動状況を確認
docker compose ps

# ログを確認（問題がある場合）
docker compose logs -f
```

## 3. Dify初期設定

### Step 1: データベース初期化（初回のみ）

初回起動時に「Internal Server Error」が表示される場合、データベースマイグレーションを実行：

```bash
# データベーステーブルを作成
docker compose exec dify-api flask db upgrade

# Difyサービスを再起動
docker compose restart dify-api dify-worker
```

### Step 2: 管理者アカウント作成

1. http://localhost にアクセス
2. 自動的に `/install` にリダイレクトされる
3. 以下を入力して「Install」をクリック：

| 項目 | 入力内容 |
|------|---------|
| Email | 管理者メールアドレス |
| Name | 管理者名 |
| Password | 8文字以上のパスワード |

### Step 3: モデル設定

1. ログイン後、右上のアイコン → **Settings**
2. **Model Provider** → **Gemini** を追加
3. `.env` に設定した `GEMINI_API_KEY` を入力

### Step 4: ナレッジベース作成

1. 左メニュー → **Knowledge**
2. **Create Knowledge** をクリック
3. 名前: `DocuSearch`（任意）
4. **Embeddingモデルの設定**（重要）：
   - ナレッジベース設定画面で **Embedding Model** を選択
   - **`gemini-embedding-001`** を選択（推奨）
   - このモデルは日本語の検索精度が高く、無料枠で利用可能

   > **注意**: デフォルトのEmbeddingモデルでは日本語検索の精度が低い場合があります。
   > `gemini-embedding-001` に変更することで、検索品質が大幅に向上します。

5. 作成後、URLからナレッジベースIDを取得：

   ```
   http://localhost/knowledge/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/...
                               ↑ この部分がDataset ID
   ```

6. `.env` の `DIFY_DATASET_ID` に設定

### Step 5: アプリ作成とAPI Key取得

Dify v1.4.0では、ナレッジベースをAPI経由で操作するために**アプリ（エージェント）を作成**し、そのAPIキーを使用します。

#### 5-1. アプリの作成

1. 上部メニューの **「スタジオ」** をクリック
2. **「最初から作成」** ボタンをクリック
3. アプリタイプを選択：
   - **チャットボット** （会話型）または
   - **エージェント** （ツール使用可能）
4. アプリ名を入力（例：`DocuSearch Agent`）
5. **「作成する」** をクリック

#### 5-2. ナレッジベースの紐付け

1. 作成したアプリの編集画面で、右側の **「コンテキスト」** セクションを探す
2. **「+ 追加」** をクリック
3. Step 4で作成した **「DocuSearch」** ナレッジベースを選択
4. **「保存」** または **「公開」** をクリック

#### 5-3. APIキーの発行

1. アプリ編集画面の左サイドバーで **「APIアクセス」** をクリック
2. 右上の **「APIキー」** ボタンをクリック
3. **「+ 新しいシークレットキーを作成」** をクリック
4. 表示されたキーをコピー（`app-` で始まる文字列）
5. `.env` ファイルの `DIFY_KNOWLEDGE_API_KEY` に設定：

   ```
   DIFY_KNOWLEDGE_API_KEY=app-xxxxxxxxxxxxxxxxxxxxxxxx
   ```

> **重要**: このAPIキーは一度しか表示されません。必ずコピーして安全な場所に保存してください。

## 4. n8n設定

n8nの詳細な設定手順は [N8N_WORKFLOW_SETUP.md](./N8N_WORKFLOW_SETUP.md) を参照してください。

### クイック設定

1. http://localhost:5678 にアクセス
2. 初回はオーナーアカウントを作成
3. ワークフローをインポート（`n8n/workflows/` フォルダ内）
4. 認証情報（Credentials）を作成

## 5. 動作確認

### 5-1. ファイルを配置

```bash
# watch/images フォルダに画像を配置
cp your_photo.jpg watch/images/

# watch/documents フォルダにドキュメントを配置
cp your_document.pdf watch/documents/
```

5分ごとのスケジュール実行でファイルが自動処理されます。

### 5-2. 処理結果の確認

1. n8n (http://localhost:5678) で実行履歴を確認
2. Dify (http://localhost) → **Knowledge** → **DocuSearch** でドキュメントが登録されていることを確認

### 5-3. 検索テスト

登録したデータが検索できることを確認します。

1. Dify (http://localhost) にアクセス
2. 左メニュー → **スタジオ** → 作成したアプリ（DocuSearch Agent）を開く
3. 右側の **「プレビュー」** パネルでテスト
4. 検索クエリを入力（例：「マンションの写真」「会議資料」など）
5. 登録したファイルに関連する回答が返ってくることを確認

> **ヒント**: 画像の場合、Gemini Visionが生成した説明文に基づいて検索されます。
> 例えば「東京タワー」が写った写真は「東京タワー」「タワー」「観光地」などで検索できます。

## サービス一覧

| サービス | ポート | 説明 |
|---------|--------|------|
| Dify Web | 3000 | RAGプラットフォームUI |
| Dify API | 5001 | REST API |
| n8n | 5678 | ワークフロー自動化 |
| Weaviate | 8080 | ベクトルデータベース |
| PostgreSQL | 5432 | メタデータDB |
| Redis | 6379 | キャッシュ |
| Nginx | 80 | リバースプロキシ |

## 検索方式とRerankerについて

### 検索方式の選択

Difyでは3つの検索方式が利用可能です：

| 検索方式 | 特徴 | Reranker |
| --------- | ------ | ---------- |
| **ベクトル検索** | 意味的な類似度で検索。推奨設定（gemini-embedding-001）で高精度 | 不要 |
| **全文検索** | キーワードマッチで検索。完全一致に強い | 不要 |
| **ハイブリッド検索** | ベクトル＋全文の組み合わせ。大規模データ向け | **必須** |

### 推奨設定

- **〜2000件程度**: ベクトル検索（gemini-embedding-001）で十分
- **2000件以上**: ハイブリッド検索 + Rerankerを検討

### Rerankerとは

Rerankerは検索結果を再順位付けするモデルです：

```text
クエリ → ベクトル検索（上位20件）→ Rerankerで再評価 → 上位3件を返す
```

**効果が高いケース:**

- 上位結果のスコアが似通っている場合
- 長文・複雑なクエリ
- 大量のドキュメントから精度高く検索したい場合

### Rerankerの有効化（オプション）

大規模データでハイブリッド検索が必要になった場合：

1. `docker-compose.yml` のXinferenceセクションのコメントを解除
2. `docker compose up -d xinference` でサービス起動
3. Xinference UI (`http://localhost:9997`) で `bge-reranker-v2-m3` モデルをデプロイ
4. Dify → Settings → Model Provider → Xinferenceを追加
5. ナレッジベース設定で「Hybrid Search」+ 「Rerank」を有効化

> **注意**: Xinferenceは約4GBのメモリを使用します。リソースに余裕がある環境で使用してください。

## 次のステップ

- [n8nワークフロー詳細設定](./N8N_WORKFLOW_SETUP.md)
- [アーキテクチャ解説](./ARCHITECTURE.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)

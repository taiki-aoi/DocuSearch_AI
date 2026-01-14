# 01_System_Architecture.md

## システム概要
本システムは、非構造化データ（ドキュメント、画像）を構造化データ（ベクトル、メタデータ）へ変換し、自然言語による高度な検索を実現するRAG（Retrieval-Augmented Generation）プラットフォームである。

---

## アーキテクチャ図

### 図1: システム概要図（経営層・非技術者向け）

シンプルな4ステップで、システムが何をするかを一目で理解できる図。

```mermaid
flowchart LR
    subgraph Input["入力"]
        DATA[("ファイル<br/>画像・PDF・文書")]
    end

    subgraph Process["自動処理"]
        AI["AI分析<br/>画像認識・テキスト抽出"]
    end

    subgraph Storage["蓄積"]
        KB[("ナレッジベース")]
    end

    subgraph Output["活用"]
        SEARCH["自然言語検索"]
    end

    DATA --> AI --> KB --> SEARCH
```

### 図2: データフロー図（技術概要）

ファイル種別ごとの処理パイプラインを示す図。

```mermaid
flowchart TB
    subgraph Sources["データソース"]
        IMG["画像<br/>JPG/PNG"]
        PDF["PDF"]
        DOC["文書<br/>DOCX/XLSX"]
        TXT["テキスト<br/>TXT/MD/CSV"]
    end

    subgraph Orchestration["n8n オーケストレーション"]
        MONITOR["ファイル監視<br/>5分間隔ポーリング"]
        ROUTER{"ファイル種別<br/>判定"}
    end

    subgraph ImagePipeline["画像処理パイプライン"]
        EXIF["EXIF抽出<br/>日時・GPS・カメラ"]
        GEO["ジオコーディング<br/>座標→住所変換"]
        VISION["Gemini Vision<br/>キャプション生成"]
    end

    subgraph DocPipeline["文書処理パイプライン"]
        GEMINI_PDF["Gemini PDF処理<br/>OCR対応"]
        DIFY_PARSE["Dify内蔵パーサー"]
        TEXT_EXT["テキスト抽出"]
    end

    subgraph RAG["Dify RAG Engine"]
        DOC_BUILD["ドキュメント構築"]
        CHUNK["チャンキング"]
        EMBED["Embedding<br/>ベクトル化"]
    end

    subgraph VectorDB["Weaviate"]
        INDEX[("インデックス<br/>保存")]
        SEMANTIC["セマンティック<br/>検索"]
    end

    %% ソースからオーケストレーション
    IMG & PDF & DOC & TXT --> MONITOR --> ROUTER

    %% 画像処理
    ROUTER -->|"画像"| EXIF --> GEO --> VISION --> DOC_BUILD

    %% 文書処理
    ROUTER -->|"PDF"| GEMINI_PDF --> DOC_BUILD
    ROUTER -->|"DOCX等"| DIFY_PARSE --> DOC_BUILD
    ROUTER -->|"テキスト"| TEXT_EXT --> DOC_BUILD

    %% RAG処理
    DOC_BUILD --> CHUNK --> EMBED --> INDEX --> SEMANTIC
```

### 図3: コンポーネント詳細図（開発者向け）

Dockerコンテナ構成とポート、依存関係を示す図。

```mermaid
flowchart TB
    subgraph External["外部"]
        USER((ユーザー))
        DROPBOX[(Dropbox)]
        LOCAL[("/watch<br/>ローカルフォルダ")]
        GEMINI_API["Gemini API<br/>（外部サービス）"]
    end

    subgraph DockerNetwork["docusearch-network"]
        subgraph Proxy["リバースプロキシ"]
            NGINX["nginx:80"]
        end

        subgraph Workflow["ワークフロー"]
            N8N["n8n:5678"]
        end

        subgraph DifyStack["Dify Stack"]
            DIFY_WEB["dify-web:3000"]
            DIFY_API["dify-api:5001"]
            DIFY_WORKER["dify-worker"]
            PLUGIN["plugin-daemon:5002"]
            SANDBOX["sandbox"]
            SSRF["ssrf-proxy"]
        end

        subgraph DataStores["データストア"]
            POSTGRES[("postgres:5432")]
            REDIS[("redis:6379")]
            WEAVIATE[("weaviate:8080")]
        end
    end

    %% ユーザーアクセス
    USER --> NGINX
    NGINX --> DIFY_WEB & DIFY_API & N8N

    %% データソース
    DROPBOX --> N8N
    LOCAL --> N8N

    %% n8n処理
    N8N <-->|"Vision/OCR"| GEMINI_API
    N8N -->|"create-by-text API"| DIFY_API

    %% Dify内部
    DIFY_API --> POSTGRES & REDIS & WEAVIATE
    DIFY_API --> PLUGIN & SANDBOX & SSRF
    DIFY_WORKER --> POSTGRES & REDIS & WEAVIATE
    PLUGIN --> POSTGRES & REDIS

    %% n8n DB
    N8N --> POSTGRES
```

### 図4: 画像処理詳細フロー（開発者向け）

画像がどのように処理されてベクトルDBに格納されるかの詳細。

```mermaid
flowchart TB
    subgraph Input["入力"]
        IMG_FILE["画像ファイル<br/>JPG/PNG"]
    end

    subgraph N8N["n8n ワークフロー"]
        READ["バイナリ読み込み"]

        subgraph EXIF_Block["EXIF処理"]
            EXIF_PARSE["EXIF抽出"]
            EXIF_DATA["・撮影日時<br/>・GPS座標<br/>・カメラ情報"]
        end

        subgraph GEO_Block["位置情報処理"]
            GPS_CHECK{"GPS<br/>あり?"}
            NOMINATIM["Nominatim API<br/>逆ジオコーディング"]
            NO_GPS["位置情報なし"]
            ADDRESS["住所テキスト"]
        end

        subgraph Vision_Block["Vision処理"]
            B64["Base64エンコード"]
            GEMINI["Gemini 2.5 Flash<br/>Vision API"]
            CAPTION["日本語キャプション"]
        end

        DOC_BUILD["ドキュメント構築"]
    end

    subgraph Document["生成ドキュメント"]
        DOC_CONTENT["■ファイル名: photo.jpg<br/>■撮影日時: 2024-01-15 14:30:00<br/>■撮影場所: 東京都渋谷区...<br/>■座標: 35.6xxx, 139.7xxx<br/>■カメラ: iPhone 15 Pro<br/>■画像内容: 青空の下、桜の..."]
    end

    subgraph Dify["Dify RAG Engine"]
        API["POST /document/create-by-text"]
        CHUNK["自動チャンキング<br/>indexing_technique: high_quality"]
        EMBED["Embedding生成<br/>推奨: gemini-embedding-001"]
    end

    subgraph Weaviate["Weaviate Vector DB"]
        VECTOR[("ベクトル保存")]
        SEARCH["セマンティック検索<br/>「桜の写真」「渋谷で撮った写真」"]
    end

    IMG_FILE --> READ --> EXIF_PARSE --> EXIF_DATA
    EXIF_DATA --> GPS_CHECK
    GPS_CHECK -->|Yes| NOMINATIM --> ADDRESS
    GPS_CHECK -->|No| NO_GPS --> ADDRESS
    EXIF_DATA --> B64 --> GEMINI --> CAPTION
    ADDRESS & CAPTION --> DOC_BUILD --> DOC_CONTENT
    DOC_CONTENT --> API --> CHUNK --> EMBED --> VECTOR --> SEARCH
```

### 図5: 検索・利用フロー（ユーザー視点）

ユーザーが自然言語で検索し、回答を得るまでの流れ。

```mermaid
flowchart TB
    subgraph User["ユーザー"]
        QUERY["自然言語クエリ<br/>「渋谷で撮った桜の写真は？」"]
    end

    subgraph DifyChat["Dify チャットボット"]
        RECEIVE["クエリ受信"]
        EMBED_Q["クエリEmbedding<br/>ベクトル化"]
        RECEIVE --> EMBED_Q
    end

    subgraph Weaviate["Weaviate Vector DB"]
        SEARCH["ベクトル類似検索"]
        RESULTS["関連ドキュメント取得<br/>Top-K件"]
        SEARCH --> RESULTS
    end

    subgraph RAG["RAG処理"]
        CONTEXT["コンテキスト構築<br/>検索結果 + クエリ"]
        LLM["LLM回答生成<br/>GPT-4o / Gemini"]
        CONTEXT --> LLM
    end

    subgraph Response["回答"]
        ANSWER["回答テキスト<br/>+ 参照元ドキュメント"]
    end

    QUERY --> RECEIVE
    EMBED_Q --> SEARCH
    RESULTS --> CONTEXT
    LLM --> ANSWER
```

### 図6: システム全体フロー（登録と検索の統合図）

データ登録フローと検索フローの両方を1つの図で表現。

```mermaid
flowchart TB
    subgraph Registration["データ登録フロー"]
        direction LR
        FILES[("ファイル<br/>画像/PDF/文書")]
        N8N["n8n<br/>オーケストレーション"]
        GEMINI["Gemini API<br/>Vision/OCR"]
        DIFY_REG["Dify API<br/>ドキュメント登録"]
    end

    subgraph Storage["ナレッジベース"]
        WEAVIATE[("Weaviate<br/>ベクトルDB")]
    end

    subgraph Search["検索・利用フロー"]
        direction LR
        USER((ユーザー))
        DIFY_CHAT["Dify<br/>チャットボット"]
        LLM["LLM<br/>回答生成"]
        ANSWER["回答"]
    end

    %% 登録フロー
    FILES --> N8N
    N8N <--> GEMINI
    N8N --> DIFY_REG
    DIFY_REG --> WEAVIATE

    %% 検索フロー
    USER --> DIFY_CHAT
    DIFY_CHAT <--> WEAVIATE
    DIFY_CHAT --> LLM
    LLM --> ANSWER
    ANSWER --> USER
```

---

## コア・コンポーネント

### 1. オーケストレーション層 (Automation)
* **Engine:** n8n (Self-hosted)
* **役割:** 外部データソース（Dropbox等）の監視、データパイプラインの制御、APIの統合。
* **処理フロー:**
    * File Polling / Webhook検知
    * 条件分岐（画像ファイル vs 文書ファイル）
    * Vision APIへのリクエスト送信
    * RAGエンジンへのデータ投入

### 2. 知能処理層 (Cognitive & Processing)
* **RAG Engine:** Dify (Open Source)
* **LLM (Inference):** * Text Generation: OpenAI GPT-4o / Gemini 2.5 Pro
    * Vision Analysis: Gemini 2.5 Flash (コストパフォーマンスと速度重視)
* **Vector Database:** Weaviate / Chroma (Dify内包または外部接続)
* **役割:** 文書のチャンク分割、Embedding（ベクトル化）、セマンティック検索、回答生成。

### 3. データソース層 (Storage)
* **Primary:** Dropbox / OneDrive / SharePoint / Local File Server (SMB)
* **Data Type:** * Document: PDF, DOCX, XLSX, TXT, MD
    * Image: JPG, PNG (Exif情報含む)

## データ処理ロジック

### A. 画像データの構造化プロセス (Image-to-Text)
画像はそのままでは検索性が低いため、以下のプロセスでテキスト情報へ変換する。
1.  **メタデータ抽出:** Exifより「撮影日時」「GPS座標」を取得。
2.  **Geocoding:** GPS座標を「住所テキスト（国・県・市・ランドマーク）」へ変換。
3.  **Vision Captioning:** マルチモーダルAIに対し、以下のプロンプトで描写を生成。
    * *Prompt:* "この画像を詳細に描写せよ。写っている物体、色、状況（食事、会議、工事現場など）、文字情報があればそれも含めてテキスト化せよ。"
4.  **Indexing:** 「ファイル名 + メタデータ + キャプション」を1つのドキュメントとしてDifyへ登録。

### B. 文書データの処理
1.  **テキスト抽出:** Dify標準のパーサーを使用。
2.  **チャンキング:** 意味のまとまりごとに500〜1000トークンで分割。
3.  **Indexing:** ベクトル化してDBへ保存。
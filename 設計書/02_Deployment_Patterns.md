# 02_Deployment_Patterns.md

## 展開モデル（Deployment Tiers）

顧客のセキュリティ要件、予算、既存インフラに応じて以下の3パターンを提供する。

### Pattern A: 完全オンプレミス (High Security / Air-Gapped)
インターネット接続が制限される製造業、金融、官公庁向け。

* **Infrastructure:** 社内物理サーバー (GPU搭載推奨: NVIDIA A100/L4等)
* **OS/Virtualization:** Linux (Ubuntu) + Docker
* **LLM Execution:** Ollama / vLLM (Local LLM: Llama 3, Qwen等を使用)
* **Network:** 社内LANのみ（インターネット遮断可）
* **Data Source:** 社内ファイルサーバー (NAS/SMB) をVolumeマウント
* **Pros:** 情報漏洩リスク・ゼロ、通信コスト固定。
* **Cons:** 初期ハードウェア投資大、モデルの性能はハードウェア依存。

### Pattern B: セキュアクラウド (Enterprise Cloud)
AWS/GCPを利用中の一般エンタープライズ企業向け。

* **Infrastructure:** AWS (ECS/Fargate) or GCP (Cloud Run)
* **Network:** * AWS Direct Connect / Site-to-Site VPN で社内LANとVPCを接続。
    * Private Linkを使用し、インターネットを経由せずAPI利用。
* **LLM:** AWS Bedrock / Vertex AI (SLAのあるエンタープライズ版API)
* **Data Source:** クラウドストレージ (S3/GCS) または VPN経由で社内サーバー参照。
* **Pros:** 高いスケーラビリティ、運用管理負荷の軽減、監査ログ対応。

### Pattern C: ライトウェイト・ハイブリッド (SaaS Integration)
中小企業、スタートアップ、部門単位での導入向け。

* **Infrastructure:** 社内PC または 小規模VPS (Docker Desktop / Portainer)
* **LLM:** OpenAI API / Gemini API (Public API利用)
* **Network:** HTTPS (Outboundのみ許可で動作可能)
* **Data Source:** Dropbox / Google Drive / OneDrive
* **Pros:** 最安、即日導入可能、プロトタイプ作成に最適。
* **Cons:** データがAPI経由で一時的に外部（LLMプロバイダ）へ送信される（学習利用はオプトアウト設定で回避）。
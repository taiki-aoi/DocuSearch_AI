# 技術実装スタック

## 1. Docker Compose 構成案（Integrated Environment）

Difyとn8nを同一ネットワーク上で稼働させ、相互通信を容易にする構成。

```yaml
version: '3'
services:
  # --- Dify Core Services (Simplified) ---
  # ※実際はDify公式のdocker-compose.ymlにあるapi, worker, web, db(Postgres), redis, weaviate等が必要
  dify-api:
    image: langgenius/dify-api:latest
    environment:
      - MODE=api
      # ... (その他の必須環境変数)
    networks:
      - rag-network

  # --- Automation & Orchestration ---
  n8n:
    image: n8n/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_ basic_auth_active=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
      - GENERIC_TIMEZONE=Asia/Tokyo
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - rag-network

networks:
  rag-network:
    driver: bridge

volumes:
  n8n_data:
```

### 2. n8n ワークフロー詳細設計 (Workflow Logic)

Dropboxから画像を検知し、Difyへ登録するまでの具体的なデータパイプライン定義。

### A. Trigger & Routing

- **Trigger:** Dropbox Node (File Created/Updated)
    - Watch Path: `/Project_Photos/*`
- **Switch:** IF File Extension is `jpg/jpeg/png` THEN -> **Image Processing Flow**
- **Switch:** IF File Extension is `pdf/docx` THEN -> **Document Flow** (Direct Upload)

### B. Image Processing Flow (Python Code Node)

n8nの「Code Node」で実行する、画像ExifデータからGPSを抽出するスクリプト。

Python

```code
# n8n Code Node (Python)
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io

def get_exif_data(image_binary):
    image = Image.open(io.BytesIO(image_binary))
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

# メイン処理（緯度経度を10進数へ変換するロジック含む）
# ... (ここに変換ロジックを実装)
# return: {"lat": 35.6895, "lon": 139.6917, "datetime": "2025:12:16 12:00:00"}
```

### C. Cognitive Processing (Vision AI)

- **Node:** HTTP Request (Gemini API)
- **Method:** POST `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **Body:**
    
    ```code
    {
      "contents": [{
        "parts": [
          {"text": "この画像を分析し、検索用のメタデータを作成してください。\n1. 写っている物体（具体的）\n2. シチュエーション（食事、会議、工事現場など）\n3. 雰囲気や色味\n出力は日本語の平文でお願いします。"},
          {"inline_data": {"mime_type": "image/jpeg", "data": "{{base64_image_data}}"}}
        ]
      }]
    }
    ```
    

### D. Indexing (Dify API)

- Node: HTTP Request (Dify Knowledge API)
- Target: Create a document from text
- Payload Construction:JSON
    
```code
{
  "name": "{{file_name}}",
  "text": "■ファイル名: {{file_name}}\n■撮影場所: {{address_from_geocoding}}\n■撮影日時: {{datetime}}\n■画像内容の説明:\n{{gemini_response_text}}",
  "indexing_technique": "high_quality",
  "process_rule": {
    "mode": "automatic"
  }
}
```
    

## 検索精度向上のためのチューニング (Optimization)

### 1. 抽象概念の検索対応 (Abstract Query)

ユーザーが「マンション」と入力した際、実際の画像に「マンション」が写っていなくてもヒットさせるため、Geminiのプロンプトに以下を含める。

- *「建物が写っている場合、その種類（マンション、ビル、戸建て、オフィス）を推測して記述に含めること。」*
- *「料理が写っている場合、ジャンル（イタリアン、和食、居酒屋）を含めること。」*

### 2. ハイブリッド検索設定

Difyの「検索設定」において、以下を推奨とする。

- **Top K:** 5 (関連性の高い5件を表示)
- **Score Threshold:** 0.5 (ノイズを排除)
- **Rerank Model:** Enable (検索結果をさらにAIが並び替える機能をONにし、精度を高める)

### 3. メタデータフィルタリング

将来的な拡張として、撮影年や場所での絞り込みを可能にするため、Difyへの登録時にテキストだけでなく「セグメント」としてメタデータを分離登録することを検討する。
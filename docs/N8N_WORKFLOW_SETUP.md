# n8n ワークフローセットアップ手順

このドキュメントでは、n8nワークフローをゼロからセットアップする手順を記載します。

## 前提条件

- Docker環境が起動している
- Difyのセットアップが完了している（ナレッジベース作成、Dataset API Key取得済み）

## Step 1: n8nへのログイン

1. <http://localhost:5678> にアクセス
2. 初回の場合はオーナーアカウントを作成

## Step 2: クレデンシャルの作成

ワークフローをインポートする前に、認証情報を設定します。

1. 左メニュー → **Credentials** → **Add Credential**
2. **Header Auth** を選択
3. 以下を入力：

| 項目 | 値 |
| ---- | -- |
| Name | `Dataset API Key` |
| Credential Data - Name | `Authorization` |
| Credential Data - Value | `Bearer dataset-xxxxxxxx`（Difyで取得したDataset API Key） |

4. **Save** をクリック

### APIキーの種類

| キー種別 | 形式 | 用途 |
| -------- | ---- | ---- |
| App API Key | `app-xxxxx` | チャットボットアプリのAPI呼び出し |
| Dataset API Key | `dataset-xxxxx` | n8nからDify Knowledge Base APIへのアクセス |

Dataset API Keyは Dify「ナレッジ」→「API ACCESS」タブから発行できます。

## Step 3: ワークフローのインポート

以下の順番でインポートします（依存関係のため順番が重要）。

### 3-1. Document Processing - DocuSearch

1. **Workflows** → **Add Workflow** → **Import from File**
2. `n8n/workflows/document-processing.json` を選択
3. インポート後、ワークフローを開いて **Save** をクリック
4. 右上の **Publish** ボタンをクリック → **Publish**

### 3-2. Image Processing - DocuSearch（特殊な手順あり）

このワークフローは `executeWorkflowTrigger` を使用しているため、特殊な公開手順が必要です。

1. **Workflows** → **Add Workflow** → **Import from File**
2. `n8n/workflows/image-processing.json` を選択
3. インポート後、ワークフローを開く
4. **Gemini Vision API** ノードをクリックして開く
5. 何も変更せずにノードを閉じる
6. **Save** をクリック
7. 右上の **Publish** ボタンをクリック

> **注意**: 「Gemini Vision API」ノードに過去の実行エラーがキャッシュされていると公開できないことがあります。その場合はノードを一度開いて閉じることでキャッシュがクリアされます。

### 3-3. Local Folder Monitor - DocuSearch

1. **Workflows** → **Add Workflow** → **Import from File**
2. `n8n/workflows/local-folder-monitor.json` を選択
3. インポート後、ワークフローを開く
4. ワークフローを **Save**
5. 右上の **Publish** ボタンをクリック → **Publish**

### 環境変数によるワークフローID管理（オプション）

> **Note**: 現在はワークフローIDをJSONファイルに直接記載しています。
> 将来的に環境変数で管理する場合は以下の手順で設定します。

1. 左メニュー → **Settings** → **Variables**
2. 以下の変数を追加：

| Variable | Value |
| -------- | ----- |
| `IMAGE_PROCESSING_WORKFLOW_ID` | Image Processing - DocuSearch のワークフローID |
| `DOCUMENT_PROCESSING_WORKFLOW_ID` | Document Processing - DocuSearch のワークフローID |

> **ワークフローIDの確認方法**: 各ワークフローを開いたときのURLから確認できます。
> `http://localhost:5678/workflow/XXXXXXXXXXXXXXXX` ← この部分がID

## Step 4: テスト実行

### 4-1. テストワークフローでの確認（推奨）

本番ワークフローを実行する前に、テストワークフローで動作確認できます。

1. `n8n/workflows/test-document-processing.json` をインポート
2. `watch/documents/test.txt` にテストファイルを配置
3. ワークフローを開いて **Test workflow** をクリック
4. 各ノードが正常に実行されることを確認

同様に `test-image-processing.json` でも確認できます。

### 4-2. Local Folder Monitorのテスト

1. Local Folder Monitor - DocuSearch を開く
2. **Test workflow** をクリック
3. 「画像ファイル一覧取得」「ドキュメント一覧取得」ノードが正常に実行されることを確認

## Step 5: 自動実行の開始

ワークフローが公開（Publish）されると、スケジュールトリガーにより5分ごとに自動実行されます。

- `watch/images/` に画像（.jpg, .jpeg, .png）を配置
- `watch/documents/` にドキュメント（.pdf, .docx, .xlsx, .txt, .md）を配置

自動的に処理され、Difyナレッジベースに登録されます。

## ワークフロー一覧

| ワークフロー | 用途 | ファイル |
| ------------ | ---- | -------- |
| Document Processing - DocuSearch | ドキュメントのDify登録 | `document-processing.json` |
| Image Processing - DocuSearch | 画像のEXIF抽出・Vision分析・Dify登録 | `image-processing.json` |
| Local Folder Monitor - DocuSearch | フォルダ監視・自動処理呼び出し | `local-folder-monitor.json` |
| TEST - Document Processing | ドキュメント処理テスト用 | `test-document-processing.json` |
| TEST - Image Processing | 画像処理テスト用 | `test-image-processing.json` |

## トラブルシューティング

### 「Module 'child_process' is disallowed」エラー

Local Folder Monitorで発生する場合、古いバージョンのJSONファイルを使用しています。
最新の `local-folder-monitor.json` を再インポートしてください。

### 「Unsupported MIME type」エラー

Image Processingで発生する場合、バイナリデータが正しく渡されていません。

1. ワークフローを削除
2. 最新の `image-processing.json` を再インポート
3. 再度公開

### サブワークフローが呼び出せない

- サブワークフロー（Document Processing, Image Processing）が**公開済み**であることを確認
- ワークフローIDが正しいことを確認

### 「Base64 decoding failed for 'filesystem-v2'」エラー

親ワークフローから子ワークフローへバイナリデータを渡す際に発生します。
Image Processingワークフローがファイルパスを受け取り、自身でファイルを読み込む設計になっていることを確認してください。

## 次のステップ

- [環境構築手順に戻る](./SETUP.md)
- [アーキテクチャ解説](./ARCHITECTURE.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)

#!/usr/bin/env python3
"""
Dify create_by_file APIでファイル名を制御できるかテスト

公式ドキュメント確認結果:
- create_by_file APIは、multipart/form-dataの filename をドキュメント名として使用
- dataパラメータにnameを含めても無視される
- 解決策: filesタプルの最初の要素でfilenameを指定する

参考: https://docs.dify.ai/api-reference/documents/create-a-document-from-a-file
"""
import requests
import os
import sys

# 設定
DIFY_API_URL = "http://localhost:5001/v1"
DATASET_ID = "c099198f-c9ea-48d6-b194-6beac4d336be"

def test_create_by_file_with_custom_name(api_key: str, file_path: str, desired_name: str):
    """
    create_by_file APIでファイル名を制御するテスト

    Args:
        api_key: Dify Dataset API Key
        file_path: アップロードするファイルのパス
        desired_name: Difyに登録する名前（相対パス形式推奨）
    """
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/document/create_by_file"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # ファイルの拡張子からMIMEタイプを推測
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv',
        '.html': 'text/html',
    }
    mime_type = mime_types.get(ext, 'application/octet-stream')

    # ファイルを開く
    with open(file_path, 'rb') as f:
        # multipart/form-dataでアップロード
        # ★ポイント: filesのタプルで (filename, file_object, content_type) を指定
        # ここでfilenameを desired_name に設定することで、Difyのドキュメント名を制御
        files = {
            'file': (desired_name, f, mime_type)
        }

        data = {
            'data': '{"indexing_technique":"high_quality","process_rule":{"mode":"automatic"}}'
        }

        print(f"URL: {url}")
        print(f"Original file: {file_path}")
        print(f"Desired document name: {desired_name}")
        print(f"MIME type: {mime_type}")
        print("Uploading...")

        response = requests.post(url, headers=headers, files=files, data=data, timeout=120)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Success!")
        print(f"Document ID: {result.get('document', {}).get('id')}")
        print(f"Batch: {result.get('batch')}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


if __name__ == "__main__":
    # API Key を入力
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("Dify Dataset API Key を入力してください: ").strip()

    if not api_key:
        print("API Key が必要です")
        sys.exit(1)

    # テストファイル（存在するファイルを指定）
    # 小さいテストファイルを作成
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(test_dir, "test_upload.txt")

    # テストファイルを作成
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("これはテストファイルです。\nドキュメント名制御のテスト。")

    print("=" * 60)
    print("Test: Dify create_by_file API with custom filename")
    print("=" * 60)

    # テスト: アンダースコアをセパレーターとして使用
    print("\n--- Test: Using '_' as separator (recommended) ---")
    result = test_create_by_file_with_custom_name(
        api_key=api_key,
        file_path=test_file,
        desired_name="documents_subfolder_test_custom_name.txt"
    )

    # テストファイル削除
    os.remove(test_file)

    if result:
        print("\n" + "=" * 60)
        print("✓ テスト成功！")
        print("Difyコンソールで 'documents/subfolder/test_custom_name.txt' という名前で")
        print("ドキュメントが登録されているか確認してください。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ テスト失敗")
        print("=" * 60)

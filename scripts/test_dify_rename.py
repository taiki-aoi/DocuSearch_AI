#!/usr/bin/env python3
"""
Dify APIでドキュメント名を変更できるかテスト
1. create_by_file でアップロード（%2F形式）
2. update APIで名前を変更（スラッシュ形式へ）
"""
import requests
import os
import sys

DIFY_API_URL = "http://localhost:5001/v1"
DATASET_ID = "c099198f-c9ea-48d6-b194-6beac4d336be"

def upload_file(api_key: str, file_path: str, encoded_name: str):
    """ファイルをアップロード（%2F形式のファイル名）"""
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/document/create_by_file"

    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, 'rb') as f:
        files = {'file': (encoded_name, f, 'text/plain')}
        data = {'data': '{"indexing_technique":"high_quality","process_rule":{"mode":"automatic"}}'}

        print(f"Uploading with filename: {encoded_name}")
        response = requests.post(url, headers=headers, files=files, data=data, timeout=120)

    if response.status_code == 200:
        result = response.json()
        doc_id = result.get('document', {}).get('id')
        print(f"Upload success! Document ID: {doc_id}")
        return doc_id
    else:
        print(f"Upload failed: {response.text}")
        return None


def rename_document(api_key: str, document_id: str, new_name: str):
    """ドキュメント名を変更"""
    # Method 1: PATCH to document endpoint
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/documents/{document_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {"name": new_name}

    print(f"\nTrying PATCH {url}")
    print(f"New name: {new_name}")

    response = requests.patch(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("Rename success!")
        return True
    else:
        print(f"PATCH failed: {response.text}")

    # Method 2: Try PUT
    print(f"\nTrying PUT {url}")
    response = requests.put(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("Rename success!")
        return True
    else:
        print(f"PUT failed: {response.text}")

    # Method 3: Try metadata endpoint
    url_meta = f"{DIFY_API_URL}/datasets/{DATASET_ID}/documents/{document_id}/metadata"
    print(f"\nTrying POST {url_meta}")

    response = requests.post(url_meta, headers=headers, json={"name": new_name}, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("Rename success via metadata!")
        return True
    else:
        print(f"Metadata failed: {response.text}")

    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("API Key: ").strip()

    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(test_dir, "test_rename.txt")

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test content for rename test")

    print("=" * 60)
    print("Test: Upload with %2F then rename to /")
    print("=" * 60)

    # Step 1: Upload with encoded name
    encoded_name = "documents%2Ftest_rename%2Ftest.txt"
    desired_name = "documents/test_rename/test.txt"

    doc_id = upload_file(api_key, test_file, encoded_name)

    if doc_id:
        # Step 2: Rename to slash format
        success = rename_document(api_key, doc_id, desired_name)

        if success:
            print("\n" + "=" * 60)
            print("SUCCESS! Document renamed to slash format")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("FAILED: Could not rename document")
            print("=" * 60)

    os.remove(test_file)

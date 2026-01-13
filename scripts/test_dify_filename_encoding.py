#!/usr/bin/env python3
"""
Dify create_by_file APIでスラッシュをエンコードして送信できるかテスト
"""
import requests
import os
import sys
import urllib.parse

DIFY_API_URL = "http://localhost:5001/v1"
DATASET_ID = "c099198f-c9ea-48d6-b194-6beac4d336be"

def test_with_encoding(api_key: str, file_path: str, desired_name: str, encoding_method: str):
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/document/create_by_file"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    with open(file_path, 'rb') as f:
        files = {
            'file': (desired_name, f, 'text/plain')
        }

        data = {
            'data': '{"indexing_technique":"high_quality","process_rule":{"mode":"automatic"}}'
        }

        print(f"Method: {encoding_method}")
        print(f"Filename sent: {desired_name}")

        response = requests.post(url, headers=headers, files=files, data=data, timeout=120)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        doc_name = result.get('document', {}).get('name', 'unknown')
        print(f"Success! Document name in Dify: {doc_name}")
        return result
    else:
        print(f"Error: {response.text[:200]}")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("API Key: ").strip()

    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(test_dir, "test_upload.txt")

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test content")

    print("=" * 60)
    print("Testing different filename encoding methods")
    print("=" * 60)

    original = "documents/subfolder/test.txt"

    # Test 1: URL encode the slash
    print("\n--- Test 1: URL encode slash (%2F) ---")
    encoded1 = original.replace("/", "%2F")
    test_with_encoding(api_key, test_file, encoded1, "URL encode")

    # Test 2: Backslash instead of forward slash
    print("\n--- Test 2: Backslash (\\) ---")
    encoded2 = original.replace("/", "\\")
    test_with_encoding(api_key, test_file, encoded2, "Backslash")

    # Test 3: Unicode slash (fullwidth)
    print("\n--- Test 3: Fullwidth slash ---")
    encoded3 = original.replace("/", "\uFF0F")  # Fullwidth solidus
    test_with_encoding(api_key, test_file, encoded3, "Fullwidth slash")

    # Test 4: Colon (like Windows path alternative)
    print("\n--- Test 4: Colon (:) ---")
    encoded4 = original.replace("/", ":")
    test_with_encoding(api_key, test_file, encoded4, "Colon")

    # Test 5: Right arrow
    print("\n--- Test 5: Arrow (>) ---")
    encoded5 = original.replace("/", ">")
    test_with_encoding(api_key, test_file, encoded5, "Arrow")

    os.remove(test_file)
    print("\n" + "=" * 60)

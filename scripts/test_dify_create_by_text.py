#!/usr/bin/env python3
"""
Dify create-by-text APIでスラッシュを含むname指定ができるかテスト
"""
import requests
import sys

DIFY_API_URL = "http://localhost:5001/v1"
DATASET_ID = "c099198f-c9ea-48d6-b194-6beac4d336be"

def test_create_by_text(api_key: str, name: str, text: str):
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/document/create-by-text"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "text": text,
        "indexing_technique": "high_quality",
        "process_rule": {
            "mode": "automatic"
        }
    }

    print(f"URL: {url}")
    print(f"Name: {name}")
    print("Uploading...")

    response = requests.post(url, headers=headers, json=payload, timeout=120)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("Success!")
        print(f"Document ID: {result.get('document', {}).get('id')}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("Dify Dataset API Key: ").strip()

    if not api_key:
        print("API Key required")
        sys.exit(1)

    print("=" * 60)
    print("Test: create-by-text API with slash in name")
    print("=" * 60)

    # Test 1: Slash separator
    print("\n--- Test 1: Using '/' in name ---")
    result1 = test_create_by_text(
        api_key=api_key,
        name="documents/subfolder/test_text.txt",
        text="Test content for slash separator"
    )

    # Test 2: Underscore separator
    print("\n--- Test 2: Using '_' in name ---")
    result2 = test_create_by_text(
        api_key=api_key,
        name="documents_subfolder_test_text.txt",
        text="Test content for underscore separator"
    )

    print("\n" + "=" * 60)
    if result1:
        print("Slash (/) works for create-by-text API!")
    else:
        print("Slash (/) does NOT work for create-by-text API")

    if result2:
        print("Underscore (_) works for create-by-text API!")
    print("=" * 60)

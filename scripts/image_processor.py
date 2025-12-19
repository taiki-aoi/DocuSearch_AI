"""
Combined Image Processor for DocuSearch_AI
Orchestrates EXIF extraction, geocoding, and prepares data for Dify indexing.
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from exif_extractor import extract_exif, extract_exif_from_file
from geocoder import Geocoder, get_geocoder


# Load environment variables
load_dotenv()


class ImageProcessor:
    """
    Process images for RAG indexing.
    Extracts metadata, geocodes location, and generates vision captions.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        geocoder: Optional[Geocoder] = None
    ):
        """
        Initialize image processor.

        Args:
            gemini_api_key: Gemini API key for vision analysis
            geocoder: Geocoder instance (auto-created if None)
        """
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY')
        self.geocoder = geocoder or get_geocoder()

        # Gemini API configuration
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        # Vision prompt for detailed image analysis (Japanese)
        self.vision_prompt = """この画像を詳細に分析し、検索用のメタデータを作成してください。以下の点を含めて記述してください：

1. 写っている物体（具体的に）
   - 建物がある場合、その種類（マンション、ビル、戸建て、オフィス、商業施設など）
   - 車両がある場合、種類（乗用車、トラック、バイクなど）
   - 人物がいる場合、人数と状況（ビジネス、カジュアル、イベントなど）

2. シチュエーション・場面
   - 食事、会議、工事現場、旅行、イベント、日常など
   - 料理がある場合、ジャンル（イタリアン、和食、中華、カフェなど）

3. 雰囲気や色味
   - 明るい、暗い、モダン、レトロ、ポップ、落ち着いた雰囲気など

4. 読み取れる文字情報
   - 看板、書籍、掲示板など読める文字があれば記述

5. 場所の推測
   - 屋内/屋外、都市/郊外/自然など

出力は日本語の自然な文章で、検索キーワード化しやすい形式でお願いします。"""

    def process_image(
        self,
        image_binary: bytes,
        filename: str,
        generate_caption: bool = True
    ) -> Dict[str, Any]:
        """
        Process an image file for indexing.

        Args:
            image_binary: Raw image bytes
            filename: Original filename
            generate_caption: Whether to generate vision caption

        Returns:
            Dictionary containing all extracted metadata and caption
        """
        result = {
            "filename": filename,
            "datetime": None,
            "location": None,
            "coordinates": None,
            "camera": None,
            "vision_caption": None,
            "metadata_text": "",
            "full_document_text": "",
            "success": True,
            "errors": []
        }

        # Step 1: Extract EXIF
        exif = extract_exif(image_binary)

        if exif.get("error"):
            result["errors"].append(f"EXIF extraction: {exif['error']}")

        # Parse datetime
        result["datetime"] = exif.get("datetime")

        # Parse camera info
        camera_parts = []
        if exif.get("camera_make"):
            camera_parts.append(exif["camera_make"])
        if exif.get("camera_model"):
            camera_parts.append(exif["camera_model"])
        if camera_parts:
            result["camera"] = " ".join(camera_parts)

        # Step 2: Geocode if GPS available
        if exif.get("has_gps") and exif.get("latitude") and exif.get("longitude"):
            result["coordinates"] = {
                "lat": exif["latitude"],
                "lon": exif["longitude"]
            }

            try:
                geo_result = self.geocoder.reverse_geocode(
                    exif["latitude"],
                    exif["longitude"]
                )
                if "error" not in geo_result:
                    result["location"] = geo_result.get("formatted", "")
                else:
                    result["errors"].append(f"Geocoding: {geo_result['error']}")
            except Exception as e:
                result["errors"].append(f"Geocoding exception: {str(e)}")

        # Step 3: Generate vision caption
        if generate_caption and self.gemini_api_key:
            try:
                caption = self._generate_vision_caption(image_binary)
                result["vision_caption"] = caption
            except Exception as e:
                result["errors"].append(f"Vision caption: {str(e)}")

        # Step 4: Build metadata text
        result["metadata_text"] = self._build_metadata_text(result)

        # Step 5: Build full document text for Dify
        result["full_document_text"] = self._build_document_text(result)

        # Set success based on whether we have usable content
        result["success"] = bool(result["metadata_text"] or result["vision_caption"])

        return result

    def process_image_file(
        self,
        file_path: str,
        generate_caption: bool = True
    ) -> Dict[str, Any]:
        """
        Process an image file from disk.

        Args:
            file_path: Path to image file
            generate_caption: Whether to generate vision caption

        Returns:
            Processing result dictionary
        """
        with open(file_path, 'rb') as f:
            image_binary = f.read()

        filename = os.path.basename(file_path)
        return self.process_image(image_binary, filename, generate_caption)

    def _generate_vision_caption(self, image_binary: bytes) -> str:
        """
        Generate image caption using Gemini Vision API.

        Args:
            image_binary: Raw image bytes

        Returns:
            Generated caption text
        """
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        # Encode image to base64
        image_base64 = base64.b64encode(image_binary).decode('utf-8')

        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }

        payload = {
            "contents": [{
                "parts": [
                    {"text": self.vision_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }

        response = requests.post(
            self.gemini_endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        # Extract caption from response
        try:
            caption = data["candidates"][0]["content"]["parts"][0]["text"]
            return caption.strip()
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse Gemini response: {e}")

    def _build_metadata_text(self, result: Dict[str, Any]) -> str:
        """Build structured metadata text from extracted data."""
        parts = [f"■ファイル名: {result['filename']}"]

        if result.get("datetime"):
            parts.append(f"■撮影日時: {result['datetime']}")

        if result.get("location"):
            parts.append(f"■撮影場所: {result['location']}")
        elif result.get("coordinates"):
            coords = result["coordinates"]
            parts.append(f"■座標: 緯度{coords['lat']}, 経度{coords['lon']}")

        if result.get("camera"):
            parts.append(f"■カメラ: {result['camera']}")

        return "\n".join(parts)

    def _build_document_text(self, result: Dict[str, Any]) -> str:
        """
        Build the full document text for Dify Knowledge Base indexing.

        Format:
        ■ファイル名: IMG_1234.jpg
        ■撮影場所: 芝公園, 港区, 東京都, 日本
        ■撮影日時: 2025-01-15 14:30:00
        ■画像内容の説明:
        [Vision AI generated caption]
        """
        parts = [result["metadata_text"]]

        if result.get("vision_caption"):
            parts.append("■画像内容の説明:")
            parts.append(result["vision_caption"])

        return "\n".join(parts)


def get_processor(
    gemini_api_key: Optional[str] = None,
    geocoder: Optional[Geocoder] = None
) -> ImageProcessor:
    """
    Factory function to create ImageProcessor instance.

    Args:
        gemini_api_key: Gemini API key (uses env var if not provided)
        geocoder: Geocoder instance (auto-created if not provided)

    Returns:
        ImageProcessor instance
    """
    return ImageProcessor(gemini_api_key=gemini_api_key, geocoder=geocoder)


# For standalone usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
        generate_caption = "--no-caption" not in sys.argv

        processor = get_processor()
        result = processor.process_image_file(file_path, generate_caption=generate_caption)

        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python image_processor.py <image_file> [--no-caption]")
        print("Example: python image_processor.py photo.jpg")
        print("\nEnvironment variables:")
        print("  GEMINI_API_KEY - Required for vision caption generation")
        print("  GOOGLE_MAPS_API_KEY - Optional, for high-accuracy geocoding")
        sys.exit(1)

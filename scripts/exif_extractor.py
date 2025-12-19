"""
EXIF Metadata Extractor for DocuSearch_AI
Extracts datetime and GPS coordinates from images.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import json
from typing import Dict, Any, Tuple, Optional


def dms_to_decimal(dms: Tuple, ref: str) -> float:
    """
    Convert GPS coordinates from DMS (Degrees, Minutes, Seconds) to decimal degrees.

    Args:
        dms: Tuple of (degrees, minutes, seconds) - each may be a fraction tuple
        ref: Reference direction ('N', 'S', 'E', 'W')

    Returns:
        Decimal degrees (negative for S and W)
    """
    def to_float(value):
        """Convert EXIF rational value to float."""
        if isinstance(value, tuple):
            return float(value[0]) / float(value[1]) if value[1] != 0 else 0.0
        return float(value)

    degrees = to_float(dms[0])
    minutes = to_float(dms[1])
    seconds = to_float(dms[2])

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    if ref in ['S', 'W']:
        decimal = -decimal

    return round(decimal, 6)


def extract_exif(image_binary: bytes) -> Dict[str, Any]:
    """
    Extract EXIF metadata from image binary data.

    Args:
        image_binary: Raw image bytes

    Returns:
        Dictionary containing:
        - datetime: Original capture datetime
        - latitude: GPS latitude in decimal degrees
        - longitude: GPS longitude in decimal degrees
        - has_gps: Boolean indicating if GPS data is present
        - camera_make: Camera manufacturer
        - camera_model: Camera model
        - orientation: Image orientation value
    """
    result = {
        "datetime": None,
        "datetime_original": None,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "has_gps": False,
        "camera_make": None,
        "camera_model": None,
        "orientation": 1,
        "error": None
    }

    try:
        image = Image.open(io.BytesIO(image_binary))
        exif_data = image._getexif()

        if not exif_data:
            result["error"] = "No EXIF data found"
            return result

        # Parse standard EXIF tags
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))

            if tag_name == "DateTime":
                result["datetime"] = value
            elif tag_name == "DateTimeOriginal":
                result["datetime_original"] = value
            elif tag_name == "Make":
                result["camera_make"] = str(value).strip()
            elif tag_name == "Model":
                result["camera_model"] = str(value).strip()
            elif tag_name == "Orientation":
                result["orientation"] = value
            elif tag_name == "GPSInfo":
                # Parse GPS data
                gps_data = {}
                for gps_tag_id in value:
                    gps_tag_name = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                    gps_data[gps_tag_name] = value[gps_tag_id]

                # Extract latitude
                if "GPSLatitude" in gps_data and "GPSLatitudeRef" in gps_data:
                    try:
                        result["latitude"] = dms_to_decimal(
                            gps_data["GPSLatitude"],
                            gps_data["GPSLatitudeRef"]
                        )
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass

                # Extract longitude
                if "GPSLongitude" in gps_data and "GPSLongitudeRef" in gps_data:
                    try:
                        result["longitude"] = dms_to_decimal(
                            gps_data["GPSLongitude"],
                            gps_data["GPSLongitudeRef"]
                        )
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass

                # Extract altitude
                if "GPSAltitude" in gps_data:
                    try:
                        alt = gps_data["GPSAltitude"]
                        if isinstance(alt, tuple):
                            result["altitude"] = float(alt[0]) / float(alt[1]) if alt[1] != 0 else None
                        else:
                            result["altitude"] = float(alt)

                        # Check altitude reference (0 = above sea level, 1 = below)
                        if gps_data.get("GPSAltitudeRef") == 1 and result["altitude"]:
                            result["altitude"] = -result["altitude"]
                    except (TypeError, ValueError):
                        pass

                if result["latitude"] is not None and result["longitude"] is not None:
                    result["has_gps"] = True

        # Use original datetime if available, otherwise use datetime
        if result["datetime_original"]:
            result["datetime"] = result["datetime_original"]

        # Format datetime for consistency (YYYY:MM:DD HH:MM:SS -> YYYY-MM-DD HH:MM:SS)
        if result["datetime"]:
            try:
                result["datetime"] = result["datetime"].replace(":", "-", 2)
            except AttributeError:
                pass

    except Exception as e:
        result["error"] = str(e)

    return result


def extract_exif_from_file(file_path: str) -> Dict[str, Any]:
    """
    Extract EXIF metadata from an image file.

    Args:
        file_path: Path to the image file

    Returns:
        EXIF metadata dictionary
    """
    with open(file_path, 'rb') as f:
        image_binary = f.read()
    return extract_exif(image_binary)


# For standalone and n8n Code Node usage
if __name__ == "__main__":
    import sys
    import base64

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Check if it's a file path or base64 data
        if arg.startswith('/') or arg.startswith('C:') or '.' in arg.split('/')[-1]:
            # File path
            result = extract_exif_from_file(arg)
        else:
            # Assume base64 encoded image
            try:
                image_data = base64.b64decode(arg)
                result = extract_exif(image_data)
            except Exception as e:
                result = {"error": f"Failed to decode base64: {e}"}

        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python exif_extractor.py <file_path or base64_data>")
        sys.exit(1)

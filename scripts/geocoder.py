"""
Geocoding utility for DocuSearch_AI
Converts GPS coordinates to human-readable addresses.
Supports Nominatim (free) and Google Maps Geocoding API.
"""

import os
import time
import json
import requests
from typing import Optional, Dict, Any


class Geocoder:
    """Geocoding service wrapper supporting multiple providers."""

    def __init__(
        self,
        provider: str = "nominatim",
        api_key: Optional[str] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize geocoder.

        Args:
            provider: 'nominatim' (free) or 'google' (requires API key)
            api_key: Google Maps API key (required for google provider)
            cache_enabled: Whether to cache results (in-memory)
        """
        self.provider = provider
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Nominatim requires 1 req/sec

    def _rate_limit(self):
        """Enforce rate limiting for API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key from coordinates (rounded to 5 decimal places)."""
        return f"{round(lat, 5)}:{round(lon, 5)}"

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Convert coordinates to address.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Dictionary containing:
            - full_address: Complete formatted address
            - country: Country name
            - prefecture: Prefecture/State/Province
            - city: City/Town/Village
            - town: Suburb/Neighbourhood
            - landmark: Nearby landmark if available
            - formatted: Formatted address for display
            - raw: Raw response data
        """
        # Check cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(lat, lon)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Call appropriate provider
        if self.provider == "nominatim":
            result = self._nominatim_reverse(lat, lon)
        elif self.provider == "google":
            result = self._google_reverse(lat, lon)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        # Cache result
        if self.cache_enabled and "error" not in result:
            self._cache[cache_key] = result

        return result

    def _nominatim_reverse(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Use OpenStreetMap Nominatim for reverse geocoding (free).

        Note: Nominatim usage policy requires:
        - Max 1 request per second
        - Valid User-Agent header
        - Attribution to OpenStreetMap
        """
        self._rate_limit()

        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "accept-language": "ja",
            "addressdetails": 1,
            "zoom": 18
        }
        headers = {
            "User-Agent": "DocuSearch_AI/1.0 (RAG Platform)"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                return {
                    "error": data["error"],
                    "formatted": f"座標: {lat}, {lon}"
                }

            address = data.get("address", {})

            return {
                "full_address": data.get("display_name", ""),
                "country": address.get("country", ""),
                "prefecture": address.get("state", address.get("province", "")),
                "city": self._extract_city(address),
                "town": address.get("suburb", address.get("neighbourhood", address.get("quarter", ""))),
                "landmark": address.get("tourism", address.get("amenity", address.get("building", ""))),
                "formatted": self._format_address_ja(address),
                "raw": address
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "formatted": f"座標: {lat}, {lon}"
            }

    def _google_reverse(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Use Google Maps Geocoding API.

        Requires: GOOGLE_MAPS_API_KEY environment variable or api_key parameter
        """
        if not self.api_key:
            raise ValueError("Google Maps API key required. Set GOOGLE_MAPS_API_KEY env var or pass api_key parameter.")

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lon}",
            "key": self.api_key,
            "language": "ja",
            "result_type": "street_address|locality|sublocality"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "OK":
                return {
                    "error": data.get("status", "Unknown error"),
                    "formatted": f"座標: {lat}, {lon}"
                }

            if not data.get("results"):
                return {
                    "error": "No results found",
                    "formatted": f"座標: {lat}, {lon}"
                }

            result = data["results"][0]
            components = {}
            for c in result.get("address_components", []):
                for t in c.get("types", []):
                    components[t] = c["long_name"]

            return {
                "full_address": result.get("formatted_address", ""),
                "country": components.get("country", ""),
                "prefecture": components.get("administrative_area_level_1", ""),
                "city": components.get("locality", components.get("sublocality_level_1", "")),
                "town": components.get("sublocality_level_2", components.get("sublocality_level_3", "")),
                "landmark": components.get("point_of_interest", components.get("premise", "")),
                "formatted": result.get("formatted_address", ""),
                "raw": components
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "formatted": f"座標: {lat}, {lon}"
            }

    def _extract_city(self, address: Dict) -> str:
        """Extract city name from various possible fields."""
        for key in ["city", "town", "village", "municipality", "county"]:
            if address.get(key):
                return address[key]
        return ""

    def _format_address_ja(self, address: Dict) -> str:
        """
        Format address in Japanese style (broad to specific).
        Example: 日本, 東京都, 渋谷区, 道玄坂
        """
        parts = []

        # Order: country -> prefecture -> city -> town -> suburb
        for key in ["country", "state", "province", "city", "town", "village",
                    "suburb", "neighbourhood", "quarter"]:
            value = address.get(key)
            if value and value not in parts:
                parts.append(value)

        if parts:
            return ", ".join(parts)
        return "住所不明"


def get_geocoder(provider: Optional[str] = None, api_key: Optional[str] = None) -> Geocoder:
    """
    Factory function to create geocoder instance.

    Args:
        provider: 'nominatim' or 'google'. If None, auto-selects based on API key availability.
        api_key: Google Maps API key (optional)

    Returns:
        Geocoder instance
    """
    api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')

    if provider is None:
        # Auto-select based on API key availability
        provider = "google" if api_key else "nominatim"

    return Geocoder(provider=provider, api_key=api_key)


# For standalone usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        api_key = sys.argv[3] if len(sys.argv) > 3 else None

        geocoder = get_geocoder(api_key=api_key)
        result = geocoder.reverse_geocode(lat, lon)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python geocoder.py <latitude> <longitude> [google_api_key]")
        print("Example: python geocoder.py 35.6895 139.6917")
        sys.exit(1)

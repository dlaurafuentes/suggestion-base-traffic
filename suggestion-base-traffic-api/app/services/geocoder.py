"""
Nominatim geocoder — converts city/state text to coordinates and bounding box.
Uses the free OpenStreetMap Nominatim API (no key required).
"""
import requests


def geocode_location(query: str, cfg: dict) -> dict | None:
    """
    Geocode a human-readable location string.

    Returns:
        {
          'lat': float, 'lng': float, 'display_name': str,
          'bbox': {'lat_min': f, 'lat_max': f, 'lon_min': f, 'lon_max': f}
        }
        or None if not found.
    """
    url = f"{cfg['NOMINATIM_URL']}/search"
    params = {
        'q': query,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1,
        'countrycodes': 'mx',   # Prioritise Mexico; remove for global search
    }
    headers = {'User-Agent': cfg['NOMINATIM_UA']}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f'[geocoder] error: {exc}')
        return None

    if not data:
        # Retry without country restriction
        params.pop('countrycodes', None)
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
        except Exception:
            return None

    if not data:
        return None

    result = data[0]
    bb = result.get('boundingbox', [])

    # Nominatim bbox order: [lat_min, lat_max, lon_min, lon_max]
    if len(bb) == 4:
        bbox = {
            'lat_min': float(bb[0]),
            'lat_max': float(bb[1]),
            'lon_min': float(bb[2]),
            'lon_max': float(bb[3]),
        }
    else:
        # Fallback: small box around center
        lat = float(result['lat'])
        lng = float(result['lon'])
        delta = 0.1
        bbox = {
            'lat_min': lat - delta,
            'lat_max': lat + delta,
            'lon_min': lng - delta,
            'lon_max': lng + delta,
        }

    return {
        'lat': float(result['lat']),
        'lng': float(result['lon']),
        'display_name': result.get('display_name', query),
        'bbox': bbox,
    }

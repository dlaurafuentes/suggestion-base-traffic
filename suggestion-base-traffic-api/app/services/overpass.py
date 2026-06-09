"""
Overpass API client — finds real OSM places within a configurable area.

Area modes (in priority order):
  1. geofence  — user-drawn polygon   → poly:"lat lng …"
  2. bbox      — Nominatim bbox       → (south,west,north,east)
  3. around    — point + radius       → around:radio,lat,lng

Resilience:
  - Three public endpoints tried in order; moves to next on 429/504/timeout.
  - In-memory TTL cache (5 min) keyed by area + giro.
  - 1 s back-off before retrying on rate-limit responses.
"""
import time
import requests
from .giro_map import GIRO_OSM_MAP

# ── Public Overpass endpoints (tried in order) ───────────────────────
_ENDPOINTS = [
    'https://overpass-api.de/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
]

# ── Simple in-memory cache ───────────────────────────────────────────
_CACHE: dict = {}
_CACHE_TTL = 300   # 5 minutes


def _cache_key(
    giro: str,
    lat: float, lng: float, radio: int,
    geofence: list | None,
    bbox: dict | None,
) -> tuple:
    if geofence and len(geofence) >= 3:
        return (giro, 'poly', tuple(tuple(p) for p in geofence))
    if bbox:
        return (giro, 'bbox',
                round(bbox['lat_min'], 4), round(bbox['lon_min'], 4),
                round(bbox['lat_max'], 4), round(bbox['lon_max'], 4))
    return (giro, round(lat, 3), round(lng, 3), radio)


def _cache_get(key: tuple):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    _CACHE.pop(key, None)
    return None


def _cache_set(key: tuple, data: list) -> None:
    _CACHE[key] = (time.time(), data)


def _build_area_filter(
    lat: float, lng: float, radio: int,
    geofence: list | None,
    bbox: dict | None,
) -> str:
    if geofence and len(geofence) >= 3:
        poly_str = ' '.join(f'{p[0]} {p[1]}' for p in geofence)
        return f'(poly:"{poly_str}")'
    if bbox:
        return (
            f'({bbox["lat_min"]},{bbox["lon_min"]},'
            f'{bbox["lat_max"]},{bbox["lon_max"]})'
        )
    return f'(around:{radio},{lat},{lng})'


# ── HTTP helper with fallback endpoints ─────────────────────────────
def _post_overpass(query: str, timeout: int = 25) -> dict:
    last_exc: Exception = Exception('No endpoint available')
    for endpoint in _ENDPOINTS:
        try:
            r = requests.post(
                endpoint,
                data={'data': query},
                timeout=timeout + 5,
                headers={'User-Agent': 'suggestion-base-traffic/1.0'},
            )
            if r.status_code == 429:
                print(f'[overpass] 429 on {endpoint}, trying next…')
                time.sleep(1)
                continue
            if r.status_code in (502, 503, 504):
                print(f'[overpass] {r.status_code} on {endpoint}, trying next…')
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            print(f'[overpass] timeout on {endpoint}, trying next…')
        except Exception as exc:
            print(f'[overpass] error on {endpoint}: {exc}')
            last_exc = exc
    raise last_exc


# ── Public API ───────────────────────────────────────────────────────

def search_places(
    giro: str,
    lat: float,
    lng: float,
    radio: int,
    cfg: dict,
    geofence: list | None = None,
    bbox: dict | None = None,
) -> list[dict]:
    """
    Query Overpass for POIs of type `giro`.

    Area of interest (first match wins):
      geofence  – user-drawn polygon
      bbox      – state/city bounding box from Nominatim
      (default) – circular radius around lat/lng
    """
    osm_tags = GIRO_OSM_MAP.get(giro)
    if not osm_tags:
        return []

    key = _cache_key(giro, lat, lng, radio, geofence, bbox)
    cached = _cache_get(key)
    if cached is not None:
        print(f'[overpass] cache hit — {giro}')
        return cached

    limit = cfg.get('MAX_PLACES', 50)
    area = _build_area_filter(lat, lng, radio, geofence, bbox)

    tag_lines = '\n'.join(
        f'  node["{t["key"]}"="{t["value"]}"]{area};\n'
        f'  way["{t["key"]}"="{t["value"]}"]{area};'
        for t in osm_tags
    )

    query = f"""
[out:json][timeout:25];
(
{tag_lines}
);
out center {limit};
"""

    try:
        data = _post_overpass(query, timeout=25)
    except Exception as exc:
        print(f'[overpass] all endpoints failed: {exc}')
        return []

    places = []
    for element in data.get('elements', []):
        elat = element.get('lat') or (element.get('center') or {}).get('lat')
        elng = element.get('lon') or (element.get('center') or {}).get('lon')

        if elat is None or elng is None:
            continue

        tags = element.get('tags', {})
        name = tags.get('name') or tags.get('name:es') or tags.get('brand')
        if not name:
            continue

        places.append({
            'id':            f"{element['type']}_{element['id']}",
            'osm_id':        element['id'],
            'osm_type':      element['type'],
            'name':          name,
            'giro':          giro,
            'lat':           float(elat),
            'lng':           float(elng),
            'address':       _build_address(tags),
            'website':       tags.get('website', tags.get('contact:website', '')),
            'phone':         tags.get('phone', tags.get('contact:phone', '')),
            'opening_hours': tags.get('opening_hours', ''),
            'brand':         tags.get('brand', ''),
            'cuisine':       tags.get('cuisine', ''),
            'wheelchair':    tags.get('wheelchair', ''),
            'stars':         tags.get('stars', ''),
        })

    _cache_set(key, places)
    return places


def _build_address(tags: dict) -> str:
    parts = []
    if tags.get('addr:street'):
        street = tags['addr:street']
        if tags.get('addr:housenumber'):
            street += ' ' + tags['addr:housenumber']
        parts.append(street)
    if tags.get('addr:suburb') or tags.get('addr:neighbourhood'):
        parts.append(tags.get('addr:suburb') or tags.get('addr:neighbourhood', ''))
    if tags.get('addr:city'):
        parts.append(tags['addr:city'])
    if tags.get('addr:postcode'):
        parts.append(tags['addr:postcode'])
    return ', '.join(filter(None, parts))

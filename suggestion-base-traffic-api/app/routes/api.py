import time
from flask import request, jsonify, current_app
from . import api_bp
from ..services.geocoder import geocode_location
from ..services.overpass import search_places
from ..services.crowd import get_crowd_data, get_popular_times
from ..services.giro_map import GIRO_TYPES

DEFAULT_RADIO = 2000   # metres
MIN_RADIO     = 500
MAX_RADIO     = 20_000


@api_bp.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'suggestion-base-traffic-api', 'version': '1.0.0'})


@api_bp.get('/giros')
def get_giros():
    return jsonify(GIRO_TYPES)


@api_bp.post('/search')
def search():
    """
    Search real places via Overpass API.

    Body (JSON):
        giros   – required list   e.g. ["cafe", "restaurant"]   (also accepts single "giro")
        estado  – required        e.g. "Veracruz"
        ciudad  – optional        e.g. "Orizaba"  (narrows the search within the state)
        radio   – optional        radius in metres, default 2000, max 20000
    """
    body = request.get_json(force=True, silent=True) or {}

    # Accept giros array or legacy single giro field
    raw_giros = body.get('giros') or []
    if not raw_giros and body.get('giro'):
        raw_giros = [body.get('giro')]
    giros  = [g.strip() for g in raw_giros if str(g).strip()][:5]  # max 5 at once

    estado = (body.get('estado') or '').strip()
    ciudad = (body.get('ciudad') or '').strip()

    try:
        radio = int(body.get('radio') or DEFAULT_RADIO)
        radio = max(MIN_RADIO, min(MAX_RADIO, radio))
    except (ValueError, TypeError):
        radio = DEFAULT_RADIO

    if not giros:
        return jsonify({'error': 'Selecciona al menos un giro'}), 400
    if not estado:
        return jsonify({'error': 'El campo "estado" es requerido'}), 400

    # Build location query — ciudad narrows within estado when provided
    parts = []
    if ciudad:
        parts.append(ciudad)
    parts.append(estado)
    parts.append('México')
    location_query = ', '.join(parts)

    cfg = current_app.config

    location = geocode_location(location_query, cfg)
    if not location:
        loc_name = ciudad or estado
        return jsonify({'error': f'No se encontró la ubicación: {loc_name}'}), 404

    # Determine search area: geofence > ciudad (around) > estado (bbox)
    raw_geo = body.get('geofence') or []
    geofence = [[float(p[0]), float(p[1])] for p in raw_geo if len(p) == 2] if raw_geo else []
    if len(geofence) < 3:
        geofence = []

    use_bbox = (not geofence and not ciudad)
    bbox     = location['bbox'] if use_bbox else None

    # Collect places from all requested giros, deduplicate by OSM id.
    # Small delay between giros (skipped for first) to stay within rate limits.
    seen_ids: set = set()
    places: list = []
    for i, giro in enumerate(giros):
        if i > 0:
            time.sleep(0.8)
        for place in search_places(
            giro, location['lat'], location['lng'], radio, cfg,
            geofence=geofence or None, bbox=bbox,
        ):
            if place['id'] not in seen_ids:
                seen_ids.add(place['id'])
                crowd = get_crowd_data(place['id'], giro)
                place.update(crowd)
                places.append(place)

    places.sort(key=lambda p: p.get('current_popularity', 0), reverse=True)

    high_crowd    = [p for p in places if p.get('is_high_crowd')]
    gaining_crowd = [p for p in places if p.get('is_gaining_crowd')]
    avg_crowd     = (
        round(sum(p.get('current_popularity', 0) for p in places) / len(places), 1)
        if places else 0
    )

    return jsonify({
        'places':              places,
        'total':               len(places),
        'high_crowd_count':    len(high_crowd),
        'gaining_crowd_count': len(gaining_crowd),
        'avg_crowd':           avg_crowd,
        'radio':               radio,
        'location':            location,
        'query':               {'giros': giros, 'estado': estado, 'ciudad': ciudad, 'radio': radio},
    })


@api_bp.get('/places/<place_id>/popular-times')
def popular_times(place_id: str):
    giro = request.args.get('giro', 'restaurant')
    return jsonify(get_popular_times(place_id, giro))


@api_bp.get('/places/<place_id>/crowd')
def crowd(place_id: str):
    giro = request.args.get('giro', 'restaurant')
    return jsonify(get_crowd_data(place_id, giro))

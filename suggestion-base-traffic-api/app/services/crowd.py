"""
Crowd / popular-times engine.

Mirrors the popularplaces-app (github.com/spykard/popularplaces-app) metric set:
  current_popularity  – % of max capacity right now  (0-100)
  usual_popularity    – typical for this weekday/hour (7-day rolling avg)
  crowd_ratio         – current / usual  (>1 = busier than usual)
  crowd_change        – Δ% vs 15 min ago (positive = gaining crowd)
  is_high_crowd       – current > 50
  is_gaining_crowd    – crowd_change > 10
  popular_times       – 7 × 24 grid [{day, day_name, data:[0..100]×24}]
  rating              – synthetic 3.5-5.0 stars per place
  time_spent          – typical visit duration in minutes
  wait_time           – estimated wait when crowd > 70%

Patterns use Google Popular Times semantics:
  100 = absolutely packed (peak of the week for that location)
  Values scaled so weekday peak is 85-95, slowest period ≈ 5-20.
  Weekend factor shifts the curve up or down per giro type.

Personality (0.90-1.10) gives each place a stable "character" derived from
its OSM ID hash so the same place always looks the same across requests.
"""

import hashlib
import random
from datetime import datetime

# ── 24-hour weekday baseline patterns (0-100) ─────────────────────────────────
# Index 0 = midnight … 23 = 11 PM
# Peak values 85-95; off-hours proportional.
_PATTERNS: dict[str, list[int]] = {
    # ── Alimentos y Bebidas ────────────────────────────────────────────────
    "restaurant":      [ 0, 0, 0, 0, 0, 0, 0, 6,20,32,45,68,92,85,68,55,62,72,88,92,82,60,38,14],
    "fast_food":       [ 0, 0, 0, 0, 0, 0, 6,18,30,42,55,72,90,80,62,58,62,75,82,88,75,62,48,25],
    "cafe":            [ 0, 0, 0, 0, 0, 0, 6,25,58,75,70,58,52,46,52,65,60,48,36,28,22,16,10, 5],
    "bar":             [42,30,14, 6, 0, 0, 0, 0, 0, 0, 0, 6,12,18,24,35,52,70,80,85,90,85,75,58],
    "pub":             [36,24,12, 6, 0, 0, 0, 0, 0, 0, 0, 6,12,18,24,35,52,70,75,80,85,80,70,52],
    "nightclub":       [70,60,42,24,12, 0, 0, 0, 0, 0, 0, 0, 0, 6,12,18,24,42,70,88,94,98,94,80],
    "food_court":      [ 0, 0, 0, 0, 0, 0, 0, 6,12,24,42,70,88,82,70,62,70,80,85,80,70,52,28, 6],
    "ice_cream":       [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,30,42,52,58,65,72,78,78,72,65,52,35,18, 6],
    # ── Comercio Alimentario ───────────────────────────────────────────────
    "supermarket":     [ 0, 0, 0, 0, 0, 0, 0,12,30,48,65,72,78,78,72,72,82,88,82,72,52,36,18, 6],
    "convenience":     [ 6, 6, 6, 6, 6, 6,12,24,36,42,48,54,60,60,54,60,65,72,65,54,42,36,24,12],
    "bakery":          [ 0, 0, 0, 0, 0, 6,24,58,75,65,58,52,46,52,58,65,65,58,52,42,28,18, 6, 0],
    "butcher":         [ 0, 0, 0, 0, 0, 0, 0,12,36,54,65,72,65,65,65,72,72,65,54,42,24,12, 0, 0],
    "greengrocer":     [ 0, 0, 0, 0, 0, 0, 6,30,54,65,65,65,60,60,60,65,65,60,48,36,24,12, 0, 0],
    "seafood":         [ 0, 0, 0, 0, 0, 0, 6,24,48,65,72,72,65,65,65,72,65,60,48,36,24,12, 0, 0],
    "deli":            [ 0, 0, 0, 0, 0, 0, 6,24,48,65,72,72,65,60,60,65,65,60,48,36,24,12, 0, 0],
    "confectionery":   [ 0, 0, 0, 0, 0, 0, 0, 6,18,30,42,54,65,65,65,72,78,78,72,65,54,42,24, 6],
    # ── Comercio General ──────────────────────────────────────────────────
    "mall":            [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,65,82,82,75,75,82,88,82,75,65,48,24, 6],
    "department_store":[ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,65,78,78,72,72,78,82,78,72,60,42,18, 0],
    "clothes":         [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,65,78,78,72,72,78,82,78,72,60,42,18, 0],
    "shoes":           [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,36,60,72,72,65,65,72,78,72,65,54,36,12, 0],
    "jewelry":         [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,65,60,60,65,72,65,60,48,30,12, 0],
    "electronics":     [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,60,72,72,65,65,72,78,72,65,54,36,12, 0],
    "mobile_phone":    [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,60,72,72,65,65,72,78,72,65,54,36,12, 0],
    "computer":        [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,42,60,72,65,65,65,72,78,72,65,48,30, 6, 0],
    "hardware":        [ 0, 0, 0, 0, 0, 0, 0,12,36,60,72,78,72,65,65,72,72,65,54,42,24,12, 0, 0],
    "furniture":       [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,65,60,65,72,72,65,60,48,30,12, 0],
    "florist":         [ 0, 0, 0, 0, 0, 0, 6,24,54,65,65,65,60,60,60,65,65,60,48,36,24,12, 0, 0],
    "toy":             [ 0, 0, 0, 0, 0, 0, 0, 0, 6,12,30,48,65,65,65,72,78,78,72,65,54,36,12, 0],
    "books":           [ 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,65,65,65,72,78,78,72,60,48,36,18, 0],
    "gift":            [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,65,65,72,78,78,72,65,54,36,18, 0],
    "optician":        [ 0, 0, 0, 0, 0, 0, 0, 0,12,36,60,72,65,65,65,72,72,65,54,42,24,12, 0, 0],
    "sports":          [ 0, 0, 0, 0, 0, 0, 0, 6,18,30,48,65,72,72,72,78,82,82,75,65,54,36,18, 0],
    "pet":             [ 0, 0, 0, 0, 0, 0, 0, 6,18,30,48,65,72,65,65,72,78,78,72,60,48,30,12, 0],
    "stationery":      [ 0, 0, 0, 0, 0, 0, 0, 6,24,54,72,78,72,65,65,72,78,78,65,54,42,24,12, 0],
    # ── Salud ─────────────────────────────────────────────────────────────
    "pharmacy":        [ 0, 0, 0, 0, 0, 0, 0, 6,36,65,72,72,65,65,72,78,78,72,60,48,36,24,12, 6],
    "hospital":        [ 0, 0, 0, 6, 6,12,24,48,75,85,82,75,70,70,75,82,75,65,54,42,30,18, 6, 0],
    "clinic":          [ 0, 0, 0, 0, 0, 0, 0, 6,42,75,82,75,70,65,70,75,75,65,48,36,24,12, 0, 0],
    "dentist":         [ 0, 0, 0, 0, 0, 0, 0, 6,30,65,75,75,70,65,65,72,72,65,48,36,24,12, 0, 0],
    "veterinary":      [ 0, 0, 0, 0, 0, 0, 0, 6,30,60,72,72,65,65,65,72,72,65,48,36,24,12, 0, 0],
    "optometrist":     [ 0, 0, 0, 0, 0, 0, 0, 0,12,36,60,72,65,65,65,72,72,65,54,36,24,12, 0, 0],
    # ── Servicios Financieros ─────────────────────────────────────────────
    "bank":            [ 0, 0, 0, 0, 0, 0, 0, 0,12,60,78,78,72,65,65,72,65,54,36,24,12, 0, 0, 0],
    "atm":             [ 6, 6, 6, 6, 6, 6,12,24,42,54,60,65,72,72,65,65,72,78,78,65,54,42,30,18],
    "bureau_de_change":[ 0, 0, 0, 0, 0, 0, 0, 6,24,54,72,78,72,65,65,72,72,65,48,36,18, 6, 0, 0],
    # ── Transporte ────────────────────────────────────────────────────────
    "fuel":            [ 6, 6, 6, 6, 6,12,24,48,60,60,60,60,60,60,60,65,72,78,72,65,54,42,24,12],
    "parking":         [ 6, 6, 6, 6, 6,12,18,36,60,72,78,78,72,65,65,78,82,88,82,72,60,42,24,12],
    "car_wash":        [ 0, 0, 0, 0, 0, 0, 0,12,30,48,65,72,65,65,65,72,78,78,65,54,36,18, 0, 0],
    "car_repair":      [ 0, 0, 0, 0, 0, 0, 0,12,36,65,78,78,65,60,65,78,78,65,48,36,18, 6, 0, 0],
    "bicycle_shop":    [ 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,65,65,65,72,78,78,65,54,42,24, 6, 0],
    "bus_station":     [12, 6, 6,12,18,36,60,75,82,72,60,54,65,75,72,60,65,75,82,82,72,60,42,24],
    # ── Ocio y Entretenimiento ────────────────────────────────────────────
    "cinema":          [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 6,12,24,48,65,72,78,82,88,92,95,90,80,70,48],
    "theatre":         [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 6,12,18,24,30,36,42,48,65,88,95,90,75,52,24],
    "gym":             [ 0, 0, 0, 0, 0, 6,24,58,72,65,60,54,48,42,42,48,65,82,92,88,72,54,30,12],
    "swimming_pool":   [ 0, 0, 0, 0, 0, 0, 6,24,48,65,72,72,78,72,72,78,82,82,72,60,48,30,12, 0],
    "park":            [ 0, 0, 0, 0, 0, 0, 6,18,30,42,54,60,60,54,54,60,65,72,72,65,54,42,24, 6],
    "bowling":         [ 0, 0, 0, 0, 0, 0, 0, 0, 6,12,24,42,60,65,72,78,82,88,92,95,90,80,65,36],
    "escape_room":     [ 0, 0, 0, 0, 0, 0, 0, 0, 0,12,24,36,54,65,72,78,82,88,92,95,90,80,65,30],
    "casino":          [36,30,18,12, 6, 6, 6,12,18,24,30,36,42,48,54,60,65,72,78,82,88,88,78,60],
    "miniature_golf":  [ 0, 0, 0, 0, 0, 0, 0, 0, 0,12,24,42,60,72,78,82,82,82,78,72,60,42,18, 0],
    # ── Alojamiento ───────────────────────────────────────────────────────
    "hotel":           [24,18,12,12,12,18,30,54,65,60,54,48,48,54,60,65,65,60,54,48,42,36,30,24],
    "hostel":          [18,12, 6, 6, 6,12,24,42,60,54,48,42,42,48,54,60,60,54,48,42,36,30,24,18],
    "motel":           [24,18,12,12,12,18,30,48,60,54,48,42,42,48,54,60,60,54,48,42,36,30,24,24],
    # ── Servicios Personales ──────────────────────────────────────────────
    "hairdresser":     [ 0, 0, 0, 0, 0, 0, 0, 6,24,54,72,78,72,65,65,72,78,78,65,54,42,24, 6, 0],
    "beauty":          [ 0, 0, 0, 0, 0, 0, 0, 6,18,42,65,78,72,65,65,72,78,78,72,60,42,24, 6, 0],
    "tattoo":          [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,30,42,54,60,65,72,78,82,82,75,65,48,24, 6],
    "dry_cleaning":    [ 0, 0, 0, 0, 0, 0, 0, 6,30,54,65,72,65,60,60,65,72,65,54,42,24,12, 0, 0],
    "laundry":         [ 0, 0, 0, 0, 0, 0, 6,18,36,54,65,72,72,65,65,72,78,78,65,54,42,30,12, 0],
    "massage":         [ 0, 0, 0, 0, 0, 0, 0, 6,18,36,54,65,72,72,72,78,82,82,78,72,60,42,18, 0],
    # ── Educación ─────────────────────────────────────────────────────────
    "school":          [ 0, 0, 0, 0, 0, 0, 6,30,75,82,82,75,65,75,82,82,72,54,36,24,12, 6, 0, 0],
    "university":      [ 0, 0, 0, 0, 0, 0, 6,24,65,82,88,88,82,75,82,88,82,72,54,36,24,18, 6, 0],
    "library":         [ 0, 0, 0, 0, 0, 0, 0, 6,24,60,78,82,75,75,75,82,82,75,65,54,36,18, 6, 0],
    "language_school": [ 0, 0, 0, 0, 0, 0, 0,12,30,54,65,65,60,65,72,78,82,88,82,72,54,36,12, 0],
    # ── Servicios Públicos ────────────────────────────────────────────────
    "post_office":     [ 0, 0, 0, 0, 0, 0, 0, 6,30,65,78,78,72,65,65,72,72,65,48,30,12, 0, 0, 0],
    "police":          [18,12, 6, 6, 6, 6,12,24,42,54,60,60,54,54,54,60,65,65,60,54,42,36,30,24],
    "fire_station":    [12, 6, 6, 6, 6, 6,12,18,30,42,48,48,42,42,42,48,54,54,48,42,36,30,18,12],
    "townhall":        [ 0, 0, 0, 0, 0, 0, 0, 6,24,60,78,78,65,65,72,78,72,60,42,24, 6, 0, 0, 0],
    "courthouse":      [ 0, 0, 0, 0, 0, 0, 0, 6,24,65,82,82,72,65,72,82,75,65,42,24, 6, 0, 0, 0],
    # ── Cultural / Turístico ──────────────────────────────────────────────
    "museum":          [ 0, 0, 0, 0, 0, 0, 0, 0, 6,18,36,60,78,82,82,82,82,75,65,54,36,18, 6, 0],
    "gallery":         [ 0, 0, 0, 0, 0, 0, 0, 0, 6,12,24,42,60,72,78,82,82,75,65,54,36,18, 6, 0],
    "monument":        [ 0, 0, 0, 0, 0, 0, 0, 6,18,36,60,78,82,78,78,82,82,75,65,54,42,30,12, 0],
    "church":          [ 0, 0, 0, 0, 0, 0, 6,24,48,65,72,72,65,60,60,65,65,60,54,48,36,24,12, 0],
}

# Weekend multiplier (Sat/Sun) per giro
_WEEKEND: dict[str, float] = {
    "restaurant": 1.12, "fast_food": 1.08, "cafe": 0.95, "bar": 1.35,
    "pub": 1.30, "nightclub": 1.55, "food_court": 1.20, "ice_cream": 1.30,
    "supermarket": 1.18, "convenience": 1.08, "bakery": 1.10, "butcher": 0.88,
    "greengrocer": 0.88, "seafood": 0.88, "deli": 0.88, "confectionery": 1.08,
    "mall": 1.38, "department_store": 1.28, "clothes": 1.22, "shoes": 1.18,
    "jewelry": 1.18, "electronics": 1.08, "mobile_phone": 1.08, "computer": 1.05,
    "hardware": 0.68, "furniture": 1.08, "florist": 1.08, "toy": 1.28,
    "books": 1.08, "gift": 1.18, "optician": 0.78, "sports": 1.18,
    "pet": 1.08, "stationery": 0.58, "pharmacy": 0.82, "hospital": 0.62,
    "clinic": 0.48, "dentist": 0.38, "veterinary": 0.68, "optometrist": 0.48,
    "bank": 0.18, "atm": 0.88, "bureau_de_change": 0.58, "fuel": 0.92,
    "parking": 1.18, "car_wash": 1.08, "car_repair": 0.58, "bicycle_shop": 1.08,
    "bus_station": 0.82, "cinema": 1.48, "theatre": 1.28, "gym": 0.82,
    "swimming_pool": 1.28, "park": 1.38, "bowling": 1.42, "escape_room": 1.38,
    "casino": 1.28, "miniature_golf": 1.38, "hotel": 1.28, "hostel": 1.22,
    "motel": 1.12, "hairdresser": 1.28, "beauty": 1.18, "tattoo": 1.08,
    "dry_cleaning": 0.38, "laundry": 0.78, "massage": 1.08, "school": 0.05,
    "university": 0.10, "library": 0.58, "language_school": 0.28,
    "post_office": 0.18, "police": 0.78, "fire_station": 1.0,
    "townhall": 0.05, "courthouse": 0.05, "museum": 1.32, "gallery": 1.22,
    "monument": 1.28, "church": 1.18,
}

# Typical visit duration ranges (min, max) in minutes per giro
_TIME_SPENT: dict[str, tuple[int, int]] = {
    "restaurant": (45, 90), "fast_food": (10, 25), "cafe": (20, 55),
    "bar": (60, 180), "pub": (60, 150), "nightclub": (120, 300),
    "food_court": (20, 45), "ice_cream": (10, 20),
    "supermarket": (20, 45), "convenience": (3, 10), "bakery": (5, 15),
    "butcher": (5, 15), "greengrocer": (5, 15), "seafood": (5, 15),
    "deli": (5, 15), "confectionery": (5, 15),
    "mall": (90, 180), "department_store": (45, 90), "clothes": (20, 50),
    "shoes": (15, 40), "jewelry": (15, 40), "electronics": (20, 50),
    "mobile_phone": (15, 30), "computer": (20, 40), "hardware": (15, 35),
    "furniture": (30, 90), "florist": (5, 15), "toy": (15, 35),
    "books": (15, 40), "gift": (10, 30), "optician": (20, 45),
    "sports": (20, 45), "pet": (15, 35), "stationery": (5, 20),
    "pharmacy": (5, 15), "hospital": (60, 240), "clinic": (30, 90),
    "dentist": (30, 60), "veterinary": (20, 45), "optometrist": (30, 60),
    "bank": (10, 30), "atm": (2, 5), "bureau_de_change": (5, 15),
    "fuel": (5, 15), "parking": (30, 120), "car_wash": (15, 45),
    "car_repair": (60, 240), "bicycle_shop": (20, 45), "bus_station": (15, 45),
    "cinema": (90, 150), "theatre": (90, 150), "gym": (45, 90),
    "swimming_pool": (45, 90), "park": (30, 120), "bowling": (60, 120),
    "escape_room": (60, 90), "casino": (60, 240), "miniature_golf": (30, 60),
    "hotel": (480, 1440), "hostel": (480, 1440), "motel": (360, 720),
    "hairdresser": (30, 90), "beauty": (45, 120), "tattoo": (60, 180),
    "dry_cleaning": (5, 10), "laundry": (30, 90), "massage": (45, 90),
    "school": (240, 480), "university": (120, 480),
    "library": (30, 120), "language_school": (60, 120),
    "post_office": (5, 20), "police": (15, 60), "fire_station": (10, 30),
    "townhall": (15, 60), "courthouse": (30, 120),
    "museum": (60, 150), "gallery": (30, 90),
    "monument": (15, 45), "church": (30, 90),
}

# Base rating (3.0-5.0) per giro — shifted up/down relative to 4.0
_RATING_BASE: dict[str, float] = {
    "restaurant": 4.1, "fast_food": 3.7, "cafe": 4.2, "bar": 3.9,
    "pub": 4.0, "nightclub": 3.8, "food_court": 3.7, "ice_cream": 4.3,
    "supermarket": 3.8, "convenience": 3.5, "bakery": 4.3, "butcher": 4.0,
    "greengrocer": 4.0, "seafood": 4.2, "deli": 4.1, "confectionery": 4.3,
    "mall": 4.0, "department_store": 3.9, "clothes": 3.8, "shoes": 3.9,
    "jewelry": 4.1, "electronics": 3.8, "mobile_phone": 3.6, "computer": 3.9,
    "hardware": 3.9, "furniture": 3.8, "florist": 4.3, "toy": 4.0,
    "books": 4.2, "gift": 4.0, "optician": 4.1, "sports": 3.9,
    "pet": 4.2, "stationery": 3.8, "pharmacy": 4.0, "hospital": 3.5,
    "clinic": 3.8, "dentist": 4.0, "veterinary": 4.3, "optometrist": 4.0,
    "bank": 3.4, "atm": 3.5, "bureau_de_change": 3.7, "fuel": 3.7,
    "parking": 3.5, "car_wash": 4.0, "car_repair": 3.9, "bicycle_shop": 4.1,
    "bus_station": 3.4, "cinema": 4.1, "theatre": 4.4, "gym": 4.0,
    "swimming_pool": 4.1, "park": 4.4, "bowling": 4.0, "escape_room": 4.4,
    "casino": 3.8, "miniature_golf": 4.2, "hotel": 4.0, "hostel": 3.9,
    "motel": 3.6, "hairdresser": 4.1, "beauty": 4.2, "tattoo": 4.3,
    "dry_cleaning": 3.9, "laundry": 3.8, "massage": 4.4, "school": 3.8,
    "university": 4.0, "library": 4.4, "language_school": 4.1,
    "post_office": 3.4, "police": 3.5, "fire_station": 4.2,
    "townhall": 3.3, "courthouse": 3.4, "museum": 4.4, "gallery": 4.3,
    "monument": 4.5, "church": 4.4,
}

DAY_NAMES    = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
_DEFAULT_PAT = [ 6, 6, 6, 6, 6, 6,12,24,42,54,60,65,65,60,60,65,72,72,65,60,48,36,24,12]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _h4(key: str) -> int:
    """4-hex-char hash → int 0-65535."""
    return int(hashlib.md5(key.encode()).hexdigest()[:4], 16)


def _personality(place_id: str) -> float:
    """
    Stable per-place crowd multiplier (0.90–1.10).
    Narrow range so no place appears artificially empty or packed.
    """
    return 0.90 + (_h4(place_id) / 65535) * 0.20


def _base(giro: str) -> list[int]:
    return _PATTERNS.get(giro, _DEFAULT_PAT)


def _day_adjusted(pattern: list[int], weekday: int, giro: str) -> list[int]:
    if weekday >= 5:
        f = _WEEKEND.get(giro, 1.0)
        return [max(0, min(100, int(v * f))) for v in pattern]
    return pattern


def _rating(place_id: str, giro: str) -> float:
    """Synthetic rating 3.0–5.0, stable per place."""
    base  = _RATING_BASE.get(giro, 4.0)
    delta = (_h4(f"{place_id}_r") / 65535 - 0.5) * 1.0   # ±0.5 around base
    return round(max(3.0, min(5.0, base + delta)), 1)


def _time_spent(place_id: str, giro: str) -> int:
    """Typical visit duration in minutes, stable per place."""
    lo, hi = _TIME_SPENT.get(giro, (15, 60))
    frac   = _h4(f"{place_id}_t") / 65535
    return int(lo + frac * (hi - lo))


# ── Public API ────────────────────────────────────────────────────────────────

def get_popular_times(place_id: str, giro: str) -> dict:
    """
    Return the 7-day × 24-hour popular-times grid.
    Shape: [{"day": 0-6, "day_name": str, "data": [int×24]}, ...]
    """
    p    = _personality(place_id)
    base = _base(giro)
    days = []

    for d in range(7):
        adjusted = _day_adjusted(base, d, giro)
        # Small per-day deterministic variance (±6 pts)
        dvar = (_h4(f"{place_id}_{d}") / 65535 - 0.5) * 12
        data = [max(0, min(100, int(v * p + dvar))) for v in adjusted]
        days.append({'day': d, 'day_name': DAY_NAMES[d], 'data': data})

    return {'popular_times': days}


def get_crowd_data(place_id: str, giro: str) -> dict:
    """
    Return live-style crowd metrics enriched with rating and time_spent.

    current_popularity  – Realistic %, 0.90-1.10× the base pattern for this hour
    usual_popularity    – 7-day average for this hour
    crowd_ratio         – current / usual
    crowd_change        – change vs 15 min ago
    is_high_crowd       – current > 50
    is_gaining_crowd    – crowd_change > 10
    wait_time           – estimated wait minutes (0 when not busy)
    rating              – synthetic 3.0-5.0 stars
    time_spent          – typical visit in minutes
    popular_times       – full 7×24 grid
    """
    now     = datetime.now()
    weekday = now.weekday()   # 0=Mon … 6=Sun
    hour    = now.hour
    minute  = now.minute

    p            = _personality(place_id)
    base         = _base(giro)
    day_adjusted = _day_adjusted(base, weekday, giro)

    # Current = pattern × personality + small live noise
    noise   = random.gauss(0, 3)
    current = max(0, min(100, int(day_adjusted[hour] * p + noise)))

    # Usual = mean of all 7 days at this hour × personality
    usual_sum = sum(_day_adjusted(base, d, giro)[hour] for d in range(7))
    usual     = max(0, min(100, int(usual_sum / 7 * p)))

    # 15 min ago: interpolate prev hour ↔ current
    prev_hour      = (hour - 1) % 24
    prev_val       = max(0, min(100, int(day_adjusted[prev_hour] * p + random.gauss(0, 2))))
    frac_of_hour   = minute / 60
    val_15min_ago  = int(prev_val * (1 - frac_of_hour * 0.25) + current * frac_of_hour * 0.25)
    crowd_change   = current - val_15min_ago
    crowd_ratio    = round(current / max(usual, 1), 2)

    # Wait time: only when crowd > 70%
    wait_time = 0
    if current > 70:
        wait_time = int((current - 70) / 6) * 2   # 0-10 min range

    pop_times = get_popular_times(place_id, giro)['popular_times']

    return {
        'current_popularity': current,
        'usual_popularity':   usual,
        'crowd_ratio':        crowd_ratio,
        'crowd_change':       crowd_change,
        'is_high_crowd':      current > 50,
        'is_gaining_crowd':   crowd_change > 10,
        'wait_time':          wait_time,
        'rating':             _rating(place_id, giro),
        'time_spent':         _time_spent(place_id, giro),
        'popular_times':      pop_times,
    }

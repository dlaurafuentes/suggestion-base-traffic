"""
Comprehensive mapping of business giros to OpenStreetMap tags.
Used by Overpass API queries to find real places.
"""

# Maps giro slug → OSM key/value pair
GIRO_OSM_MAP: dict[str, list[dict[str, str]]] = {
    # ── Alimentos y Bebidas ──────────────────────────────────────────────
    "restaurant":    [{"key": "amenity",  "value": "restaurant"}],
    "fast_food":     [{"key": "amenity",  "value": "fast_food"}],
    "cafe":          [{"key": "amenity",  "value": "cafe"},
                      {"key": "shop",     "value": "coffee"}],         # shop=coffee es alias común
    "bar":           [{"key": "amenity",  "value": "bar"}],
    "nightclub":     [{"key": "amenity",  "value": "nightclub"},
                      {"key": "amenity",  "value": "music_venue"}],
    "food_court":    [{"key": "amenity",  "value": "food_court"}],
    "ice_cream":     [{"key": "amenity",  "value": "ice_cream"}],
    "pub":           [{"key": "amenity",  "value": "pub"}],

    # ── Comercio Alimentario ──────────────────────────────────────────────
    "supermarket":   [{"key": "shop",     "value": "supermarket"}],
    "convenience":   [{"key": "shop",     "value": "convenience"},
                      {"key": "shop",     "value": "kiosk"}],
    "bakery":        [{"key": "shop",     "value": "bakery"},
                      {"key": "shop",     "value": "pastry"}],
    "butcher":       [{"key": "shop",     "value": "butcher"}],
    "greengrocer":   [{"key": "shop",     "value": "greengrocer"},
                      {"key": "shop",     "value": "fruits_vegetables"}],
    "seafood":       [{"key": "shop",     "value": "seafood"}],
    "deli":          [{"key": "shop",     "value": "deli"}],
    "confectionery": [{"key": "shop",     "value": "confectionery"},
                      {"key": "shop",     "value": "candy"}],

    # ── Comercio General ──────────────────────────────────────────────────
    "mall":          [{"key": "shop",     "value": "mall"}],
    "department_store": [{"key": "shop",  "value": "department_store"}],
    "clothes":       [{"key": "shop",     "value": "clothes"}],
    "shoes":         [{"key": "shop",     "value": "shoes"}],
    "jewelry":       [{"key": "shop",     "value": "jewelry"},
                      {"key": "shop",     "value": "jewellery"}],
    "electronics":   [{"key": "shop",     "value": "electronics"}],
    "mobile_phone":  [{"key": "shop",     "value": "mobile_phone"}],
    "computer":      [{"key": "shop",     "value": "computer"}],
    "hardware":      [{"key": "shop",     "value": "hardware"}],
    "furniture":     [{"key": "shop",     "value": "furniture"}],
    "florist":       [{"key": "shop",     "value": "florist"}],
    "toy":           [{"key": "shop",     "value": "toys"},
                      {"key": "shop",     "value": "toy"}],
    "books":         [{"key": "shop",     "value": "books"}],
    "gift":          [{"key": "shop",     "value": "gift"},
                      {"key": "shop",     "value": "souvenir"}],
    "optician":      [{"key": "shop",     "value": "optician"}],
    "sports":        [{"key": "shop",     "value": "sports"}],
    "pet":           [{"key": "shop",     "value": "pet"},
                      {"key": "amenity",  "value": "veterinary"}],
    "stationery":    [{"key": "shop",     "value": "stationery"}],

    # ── Salud ─────────────────────────────────────────────────────────────
    "pharmacy":      [{"key": "amenity",  "value": "pharmacy"}],
    "hospital":      [{"key": "amenity",  "value": "hospital"}],
    "clinic":        [{"key": "amenity",  "value": "clinic"},
                      {"key": "healthcare","value": "clinic"}],
    "dentist":       [{"key": "amenity",  "value": "dentist"},
                      {"key": "healthcare","value": "dentist"}],
    "veterinary":    [{"key": "amenity",  "value": "veterinary"}],
    "optometrist":   [{"key": "healthcare","value": "optometrist"},
                      {"key": "shop",     "value": "optician"}],

    # ── Servicios Financieros ─────────────────────────────────────────────
    "bank":          [{"key": "amenity",  "value": "bank"}],
    "atm":           [{"key": "amenity",  "value": "atm"}],
    "bureau_de_change": [{"key": "amenity","value": "bureau_de_change"}],

    # ── Transporte ────────────────────────────────────────────────────────
    "fuel":          [{"key": "amenity",  "value": "fuel"}],
    "parking":       [{"key": "amenity",  "value": "parking"}],
    "car_wash":      [{"key": "amenity",  "value": "car_wash"}],
    "car_repair":    [{"key": "shop",     "value": "car_repair"},
                      {"key": "shop",     "value": "tyres"}],
    "bicycle_shop":  [{"key": "shop",     "value": "bicycle"}],
    "bus_station":   [{"key": "amenity",  "value": "bus_station"}],

    # ── Ocio y Entretenimiento ────────────────────────────────────────────
    "cinema":        [{"key": "amenity",  "value": "cinema"}],
    "theatre":       [{"key": "amenity",  "value": "theatre"}],
    "gym":           [{"key": "leisure",  "value": "fitness_centre"},
                      {"key": "leisure",  "value": "sports_centre"}],
    "swimming_pool": [{"key": "leisure",  "value": "swimming_pool"}],
    "park":          [{"key": "leisure",  "value": "park"}],
    "bowling":       [{"key": "leisure",  "value": "bowling_alley"}],
    "escape_room":   [{"key": "leisure",  "value": "amusement_arcade"}],
    "casino":        [{"key": "amenity",  "value": "casino"}],
    "miniature_golf":[{"key": "leisure",  "value": "miniature_golf"}],

    # ── Alojamiento ───────────────────────────────────────────────────────
    "hotel":         [{"key": "tourism",  "value": "hotel"}],
    "hostel":        [{"key": "tourism",  "value": "hostel"}],
    "motel":         [{"key": "tourism",  "value": "motel"}],
    "apartment":     [{"key": "tourism",  "value": "apartment"}],

    # ── Servicios Personales ──────────────────────────────────────────────
    "hairdresser":   [{"key": "shop",     "value": "hairdresser"},
                      {"key": "shop",     "value": "barber"}],
    "beauty":        [{"key": "shop",     "value": "beauty"},
                      {"key": "shop",     "value": "cosmetics"}],
    "tattoo":        [{"key": "shop",     "value": "tattoo"}],
    "dry_cleaning":  [{"key": "shop",     "value": "dry_cleaning"},
                      {"key": "shop",     "value": "clothes_cleaning"}],
    "laundry":       [{"key": "shop",     "value": "laundry"}],
    "massage":       [{"key": "leisure",  "value": "massage"},
                      {"key": "shop",     "value": "massage"}],

    # ── Educación ─────────────────────────────────────────────────────────
    "school":        [{"key": "amenity",  "value": "school"}],
    "university":    [{"key": "amenity",  "value": "university"},
                      {"key": "amenity",  "value": "college"}],
    "library":       [{"key": "amenity",  "value": "library"}],
    "language_school":[{"key": "amenity", "value": "language_school"}],

    # ── Servicios Públicos / Gobierno ─────────────────────────────────────
    "post_office":   [{"key": "amenity",  "value": "post_office"}],
    "police":        [{"key": "amenity",  "value": "police"}],
    "fire_station":  [{"key": "amenity",  "value": "fire_station"}],
    "courthouse":    [{"key": "amenity",  "value": "courthouse"}],
    "townhall":      [{"key": "amenity",  "value": "townhall"}],

    # ── Religioso / Cultural ──────────────────────────────────────────────
    "church":        [{"key": "amenity",  "value": "place_of_worship"}],
    "museum":        [{"key": "tourism",  "value": "museum"}],
    "gallery":       [{"key": "tourism",  "value": "gallery"},
                      {"key": "tourism",  "value": "artwork"}],
    "monument":      [{"key": "historic", "value": "monument"},
                      {"key": "historic", "value": "memorial"}],
}


# Full catalog with display metadata, grouped by category
GIRO_TYPES: list[dict] = [
    # ── Alimentos y Bebidas
    {"value": "restaurant",    "label": "Restaurante",              "icon": "🍽️",  "category": "Alimentos y Bebidas"},
    {"value": "fast_food",     "label": "Comida Rápida",            "icon": "🍔",  "category": "Alimentos y Bebidas"},
    {"value": "cafe",          "label": "Café / Cafetería",         "icon": "☕",  "category": "Alimentos y Bebidas"},
    {"value": "bar",           "label": "Bar / Cantina",            "icon": "🍺",  "category": "Alimentos y Bebidas"},
    {"value": "pub",           "label": "Pub",                      "icon": "🍻",  "category": "Alimentos y Bebidas"},
    {"value": "nightclub",     "label": "Antro / Discoteca",        "icon": "🎵",  "category": "Alimentos y Bebidas"},
    {"value": "food_court",    "label": "Plaza Gastronómica",       "icon": "🏪",  "category": "Alimentos y Bebidas"},
    {"value": "ice_cream",     "label": "Heladería / Nieve",        "icon": "🍦",  "category": "Alimentos y Bebidas"},
    # ── Comercio Alimentario
    {"value": "supermarket",   "label": "Supermercado",             "icon": "🛒",  "category": "Comercio Alimentario"},
    {"value": "convenience",   "label": "Tienda de Conveniencia",   "icon": "🏬",  "category": "Comercio Alimentario"},
    {"value": "bakery",        "label": "Panadería / Pastelería",   "icon": "🥐",  "category": "Comercio Alimentario"},
    {"value": "butcher",       "label": "Carnicería",               "icon": "🥩",  "category": "Comercio Alimentario"},
    {"value": "greengrocer",   "label": "Verdulería / Frutería",    "icon": "🥦",  "category": "Comercio Alimentario"},
    {"value": "seafood",       "label": "Pescadería / Mariscos",    "icon": "🦞",  "category": "Comercio Alimentario"},
    {"value": "deli",          "label": "Delicatessen / Charcutería","icon": "🧀", "category": "Comercio Alimentario"},
    {"value": "confectionery", "label": "Dulcería / Chocolatería",  "icon": "🍬",  "category": "Comercio Alimentario"},
    # ── Comercio General
    {"value": "mall",          "label": "Centro Comercial",         "icon": "🏢",  "category": "Comercio General"},
    {"value": "department_store","label": "Tienda Departamental",   "icon": "🏬",  "category": "Comercio General"},
    {"value": "clothes",       "label": "Ropa / Moda",              "icon": "👗",  "category": "Comercio General"},
    {"value": "shoes",         "label": "Zapatería",                "icon": "👟",  "category": "Comercio General"},
    {"value": "jewelry",       "label": "Joyería / Bisutería",      "icon": "💍",  "category": "Comercio General"},
    {"value": "electronics",   "label": "Electrónica",              "icon": "💻",  "category": "Comercio General"},
    {"value": "mobile_phone",  "label": "Telefonía / Celulares",    "icon": "📱",  "category": "Comercio General"},
    {"value": "computer",      "label": "Computadoras / TI",        "icon": "🖥️", "category": "Comercio General"},
    {"value": "hardware",      "label": "Ferretería / Tlapalería",  "icon": "🔧",  "category": "Comercio General"},
    {"value": "furniture",     "label": "Mueblería",                "icon": "🪑",  "category": "Comercio General"},
    {"value": "florist",       "label": "Floristería",              "icon": "💐",  "category": "Comercio General"},
    {"value": "toy",           "label": "Juguetería",               "icon": "🧸",  "category": "Comercio General"},
    {"value": "books",         "label": "Librería / Papelería",     "icon": "📚",  "category": "Comercio General"},
    {"value": "gift",          "label": "Regalos / Souvenirs",      "icon": "🎁",  "category": "Comercio General"},
    {"value": "optician",      "label": "Óptica",                   "icon": "👓",  "category": "Comercio General"},
    {"value": "sports",        "label": "Deportes / Artículos",     "icon": "⚽",  "category": "Comercio General"},
    {"value": "pet",           "label": "Mascotas / Veterinaria",   "icon": "🐾",  "category": "Comercio General"},
    {"value": "stationery",    "label": "Papelería / Oficina",      "icon": "✏️", "category": "Comercio General"},
    # ── Salud
    {"value": "pharmacy",      "label": "Farmacia",                 "icon": "💊",  "category": "Salud"},
    {"value": "hospital",      "label": "Hospital",                 "icon": "🏥",  "category": "Salud"},
    {"value": "clinic",        "label": "Clínica / Consultorio",    "icon": "🩺",  "category": "Salud"},
    {"value": "dentist",       "label": "Dentista / Odontología",   "icon": "🦷",  "category": "Salud"},
    {"value": "veterinary",    "label": "Veterinaria",              "icon": "🐶",  "category": "Salud"},
    {"value": "optometrist",   "label": "Optometrista",             "icon": "👁️", "category": "Salud"},
    # ── Servicios Financieros
    {"value": "bank",          "label": "Banco",                    "icon": "🏦",  "category": "Servicios Financieros"},
    {"value": "atm",           "label": "Cajero Automático (ATM)",  "icon": "🏧",  "category": "Servicios Financieros"},
    {"value": "bureau_de_change","label": "Casa de Cambio",         "icon": "💱",  "category": "Servicios Financieros"},
    # ── Transporte y Movilidad
    {"value": "fuel",          "label": "Gasolinera",               "icon": "⛽",  "category": "Transporte y Movilidad"},
    {"value": "parking",       "label": "Estacionamiento",          "icon": "🅿️", "category": "Transporte y Movilidad"},
    {"value": "car_wash",      "label": "Autolavado",               "icon": "🚿",  "category": "Transporte y Movilidad"},
    {"value": "car_repair",    "label": "Taller Mecánico",          "icon": "🔩",  "category": "Transporte y Movilidad"},
    {"value": "bicycle_shop",  "label": "Bicicletas",               "icon": "🚲",  "category": "Transporte y Movilidad"},
    {"value": "bus_station",   "label": "Central de Autobuses",     "icon": "🚌",  "category": "Transporte y Movilidad"},
    # ── Ocio y Entretenimiento
    {"value": "cinema",        "label": "Cine",                     "icon": "🎬",  "category": "Ocio y Entretenimiento"},
    {"value": "theatre",       "label": "Teatro / Auditorio",       "icon": "🎭",  "category": "Ocio y Entretenimiento"},
    {"value": "gym",           "label": "Gimnasio",                 "icon": "💪",  "category": "Ocio y Entretenimiento"},
    {"value": "swimming_pool", "label": "Alberca / Balneario",      "icon": "🏊",  "category": "Ocio y Entretenimiento"},
    {"value": "park",          "label": "Parque",                   "icon": "🌳",  "category": "Ocio y Entretenimiento"},
    {"value": "bowling",       "label": "Boliche",                  "icon": "🎳",  "category": "Ocio y Entretenimiento"},
    {"value": "escape_room",   "label": "Escape Room / Arcade",     "icon": "🎮",  "category": "Ocio y Entretenimiento"},
    {"value": "casino",        "label": "Casino",                   "icon": "🎰",  "category": "Ocio y Entretenimiento"},
    # ── Alojamiento
    {"value": "hotel",         "label": "Hotel",                    "icon": "🏨",  "category": "Alojamiento"},
    {"value": "hostel",        "label": "Hostal",                   "icon": "🛏️", "category": "Alojamiento"},
    {"value": "motel",         "label": "Motel",                    "icon": "🏩",  "category": "Alojamiento"},
    # ── Servicios Personales
    {"value": "hairdresser",   "label": "Peluquería / Barbería",    "icon": "💈",  "category": "Servicios Personales"},
    {"value": "beauty",        "label": "Salón de Belleza / Spa",   "icon": "💅",  "category": "Servicios Personales"},
    {"value": "tattoo",        "label": "Tatuajes / Piercing",      "icon": "🖋️", "category": "Servicios Personales"},
    {"value": "dry_cleaning",  "label": "Tintorería",               "icon": "👔",  "category": "Servicios Personales"},
    {"value": "laundry",       "label": "Lavandería",               "icon": "🧺",  "category": "Servicios Personales"},
    {"value": "massage",       "label": "Masajes / Spa",            "icon": "💆",  "category": "Servicios Personales"},
    # ── Educación
    {"value": "school",        "label": "Escuela / Colegio",        "icon": "🏫",  "category": "Educación"},
    {"value": "university",    "label": "Universidad / Tecnológico", "icon": "🎓", "category": "Educación"},
    {"value": "library",       "label": "Biblioteca",               "icon": "📖",  "category": "Educación"},
    {"value": "language_school","label": "Centro de Idiomas",       "icon": "🗣️", "category": "Educación"},
    # ── Servicios Públicos
    {"value": "post_office",   "label": "Correos / Paquetería",     "icon": "📮",  "category": "Servicios Públicos"},
    {"value": "police",        "label": "Policía / Seguridad",      "icon": "🚔",  "category": "Servicios Públicos"},
    {"value": "townhall",      "label": "Presidencia / Ayuntamiento","icon": "🏛️","category": "Servicios Públicos"},
    {"value": "courthouse",    "label": "Juzgado / Tribunal",       "icon": "⚖️", "category": "Servicios Públicos"},
    # ── Cultural y Turístico
    {"value": "museum",        "label": "Museo",                    "icon": "🏛️", "category": "Cultural y Turístico"},
    {"value": "gallery",       "label": "Galería de Arte",          "icon": "🖼️", "category": "Cultural y Turístico"},
    {"value": "monument",      "label": "Monumento / Sitio Histórico","icon": "🗿","category": "Cultural y Turístico"},
    {"value": "church",        "label": "Iglesia / Templo",         "icon": "⛪",  "category": "Cultural y Turístico"},
]

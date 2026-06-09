import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org'
    NOMINATIM_UA = 'suggestion-base-traffic/1.0 (open-source)'
    OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
    MAX_PLACES = 50
    CACHE_TTL = 900  # 15 min


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

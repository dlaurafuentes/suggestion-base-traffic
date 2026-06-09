# Suggestion Base Traffic

Aplicación web para buscar lugares en ciudades de México y consultar su nivel de afluencia en tiempo real, basada en datos abiertos de OpenStreetMap.

## ¿Qué hace?

1. El usuario selecciona uno o varios **giros** (tipo de negocio: restaurante, farmacia, gimnasio, etc.), un **estado** y opcionalmente una **ciudad** y un **radio de búsqueda**.
2. El backend localiza la zona via **Nominatim** (geocodificación) y consulta **Overpass API** para obtener lugares reales del mapa.
3. Cada lugar regresa enriquecido con métricas de **afluencia simulada** (inspiradas en Google Popular Times):
   - `current_popularity` — porcentaje de ocupación actual (0-100)
   - `usual_popularity` — promedio típico para este día/hora
   - `crowd_ratio` — qué tan lleno está vs. lo normal
   - `crowd_change` — tendencia vs. hace 15 minutos
   - `popular_times` — grilla 7 días × 24 horas
   - `rating`, `time_spent`, `wait_time`
4. El frontend muestra los resultados en **tarjetas**, una **gráfica de afluencia** (Chart.js) y un **mapa interactivo** (Leaflet).

## Arquitectura

```
suggestion-base-traffic/
├── suggestion-base-traffic-api/   # Backend  — Python 3 + Flask
│   ├── app/
│   │   ├── routes/api.py          # Endpoints REST
│   │   └── services/
│   │       ├── geocoder.py        # Nominatim → coordenadas
│   │       ├── overpass.py        # Overpass API → lugares OSM
│   │       ├── crowd.py           # Motor de afluencia
│   │       └── giro_map.py        # Catálogo de giros
│   ├── config.py
│   ├── run.py
│   └── requirements.txt
└── suggestion-base-traffic-web/   # Frontend — Angular 17
    └── src/app/
        ├── components/            # search-form, place-card, crowd-chart, results-map
        └── services/places.service.ts
```

## Requisitos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.11 |
| Node.js | 18 |
| Angular CLI | 17 |

## Instalación

**Backend**
```bash
cd suggestion-base-traffic-api
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
```

**Frontend**
```bash
cd suggestion-base-traffic-web
npm install
```

## Configuración

Edita `suggestion-base-traffic-api/.env`:

```env
SECRET_KEY=cambia-esto-en-produccion
FLASK_ENV=development
PORT=5000
```

No se requieren API keys — el proyecto usa únicamente APIs gratuitas de OpenStreetMap.

## Ejecución

**Backend** (puerto 5000)
```bash
cd suggestion-base-traffic-api
venv\Scripts\activate
python run.py
```

**Frontend** (puerto 4200)
```bash
cd suggestion-base-traffic-web
npm start
```

Abre `http://localhost:4200` en el navegador.

## API REST

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/health` | Estado del servicio |
| `GET` | `/api/giros` | Catálogo de tipos de negocio |
| `POST` | `/api/search` | Buscar lugares con afluencia |
| `GET` | `/api/places/:id/crowd` | Métricas de afluencia de un lugar |
| `GET` | `/api/places/:id/popular-times` | Grilla 7×24 de un lugar |

### Ejemplo `/api/search`

```json
{
  "giros": ["cafe", "restaurant"],
  "estado": "Veracruz",
  "ciudad": "Orizaba",
  "radio": 2000
}
```

## Tecnologías

- **Backend:** Flask 3, python-dotenv, Requests
- **Frontend:** Angular 17, Bootstrap 5, Leaflet, Chart.js
- **APIs externas:** Nominatim (geocoding), Overpass API (lugares OSM)

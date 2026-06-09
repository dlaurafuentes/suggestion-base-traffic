export interface DayPopularity {
  day: number;
  day_name: string;
  data: number[];   // 24 values, one per hour
}

export interface BoundingBox {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
}

export interface LocationResult {
  lat: number;
  lng: number;
  display_name: string;
  bbox: BoundingBox;
}

export interface Place {
  id: string;
  osm_id: number;
  osm_type: string;
  name: string;
  giro: string;
  lat: number;
  lng: number;
  address: string;
  website: string;
  phone: string;
  opening_hours: string;
  brand: string;
  cuisine: string;
  wheelchair: string;
  stars: string;

  // Crowd metrics (mirror popularplaces-app)
  current_popularity: number;
  usual_popularity: number;
  crowd_ratio: number;
  crowd_change: number;
  is_high_crowd: boolean;
  is_gaining_crowd: boolean;
  wait_time: number;
  rating: number;
  time_spent: number;
  popular_times: DayPopularity[];
}

export interface SearchRequest {
  giros: string[];                // required, at least one
  estado: string;                 // required
  ciudad?: string;                // optional — narrows within estado
  radio?: number;                 // optional — metres, default 2000
  geofence?: [number, number][];  // optional — drawn polygon [[lat,lng],…]
}

export interface SearchResponse {
  places: Place[];
  total: number;
  high_crowd_count: number;
  gaining_crowd_count: number;
  avg_crowd: number;
  radio: number;
  location: LocationResult;
  query: SearchRequest;
}

export interface GiroType {
  value: string;
  label: string;
  icon: string;
  category: string;
}

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SearchFormComponent } from './components/search-form/search-form.component';
import { ResultsMapComponent } from './components/results-map/results-map.component';
import { PlaceCardComponent } from './components/place-card/place-card.component';
import { CrowdChartComponent } from './components/crowd-chart/crowd-chart.component';
import { PlacesService } from './services/places.service';
import { Place, SearchRequest, SearchResponse } from './models/place.model';

interface QuadrantData {
  name: string;
  places: Place[];
  avgCrowd: number;
  lowCrowdCount: number;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    SearchFormComponent,
    ResultsMapComponent,
    PlaceCardComponent,
    CrowdChartComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  response: SearchResponse | null = null;
  selectedPlace: Place | null = null;
  loading = false;
  error: string | null = null;

  // Filter / sort state
  sortKey: 'current_popularity' | 'usual_popularity' | 'crowd_ratio' | 'name' = 'current_popularity';
  filterHigh    = false;
  filterGaining = false;

  // Geofence
  drawnGeofence: [number, number][] | null = null;

  // Hour selector (00–23 h)
  readonly hours = Array.from({ length: 24 }, (_, i) => i);
  selectedHour: number | null = null;

  constructor(private svc: PlacesService) {}

  // ── Search ──────────────────────────────────────────────────────

  onSearch(req: SearchRequest) {
    if (this.drawnGeofence?.length) {
      req = { ...req, geofence: this.drawnGeofence };
    }
    this.loading      = true;
    this.error        = null;
    this.response     = null;
    this.selectedPlace = null;
    this.selectedHour  = null;

    this.svc.search(req).subscribe({
      next: r => { this.response = r; this.loading = false; },
      error: e => {
        this.error = this.parseError(e);
        this.loading = false;
      },
    });
  }

  private parseError(e: any): string {
    if (e?.status === 0)   return 'No se pudo conectar con el servidor. Verifica que el backend esté activo en el puerto 5000.';
    if (e?.status === 404) return e?.error?.error ?? 'No se encontró la ubicación solicitada.';
    if (e?.status === 429) return 'Demasiadas solicitudes a Overpass API. Espera unos segundos e intenta de nuevo.';
    if (e?.status >= 500)  return 'Error interno del servidor. Intenta de nuevo en unos momentos.';
    return e?.error?.error ?? e?.message ?? 'Error al buscar. Intenta de nuevo.';
  }

  resetSearch() {
    this.response      = null;
    this.selectedPlace = null;
    this.error         = null;
    this.filterHigh    = false;
    this.filterGaining = false;
    this.sortKey       = 'current_popularity';
    this.selectedHour  = null;
    this.drawnGeofence = null;
  }

  selectPlace(place: Place) {
    this.selectedPlace = place;
    setTimeout(() => {
      document.getElementById('detail-anchor')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }

  onGeofenceDrawn(coords: [number, number][] | null) {
    this.drawnGeofence = coords;
  }

  // ── Hour helpers ────────────────────────────────────────────────

  fmtHour(h: number): string {
    return h.toString().padStart(2, '0');
  }

  isHighHourOnAvg(h: number): boolean {
    const places = this.response?.places;
    if (!places?.length) return false;
    const today = new Date().getDay();
    let sum = 0, n = 0;
    for (const p of places) {
      const d = p.popular_times?.find(d => d.day === today);
      if (d?.data?.[h] !== undefined) { sum += d.data[h]; n++; }
    }
    return n > 0 && sum / n > 66;
  }

  // ── Selected place resolved against current viewPlaces ──────────

  get currentSelectedPlace(): Place | null {
    if (!this.selectedPlace) return null;
    return this.viewPlaces.find(p => p.id === this.selectedPlace!.id) ?? this.selectedPlace;
  }

  // ── View places (respects hour selector) ────────────────────────

  get viewPlaces(): Place[] {
    if (!this.response?.places.length) return [];
    if (this.selectedHour === null) return this.response.places;

    const today = new Date().getDay();
    const h = this.selectedHour;
    return this.response.places.map(p => {
      const d = p.popular_times?.find(d => d.day === today);
      const val = d?.data?.[h] ?? p.current_popularity;
      const ratio = p.usual_popularity > 0
        ? Math.round((val / p.usual_popularity) * 10) / 10
        : 1;
      return {
        ...p,
        current_popularity: val,
        crowd_ratio: ratio,
        crowd_change: 0,
        is_high_crowd: val > 66,
        is_gaining_crowd: false,
      };
    });
  }

  // ── Filtered + sorted list ──────────────────────────────────────

  get filteredPlaces(): Place[] {
    let list = [...this.viewPlaces];
    if (this.filterHigh)    list = list.filter(p => p.is_high_crowd);
    if (this.filterGaining) list = list.filter(p => p.is_gaining_crowd);
    if (this.sortKey === 'name') {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      list.sort((a, b) => (b[this.sortKey] as number) - (a[this.sortKey] as number));
    }
    return list;
  }

  // ── Zone recommendation ─────────────────────────────────────────

  get bestPickNow(): Place | null {
    if (!this.viewPlaces.length) return null;
    return [...this.viewPlaces]
      .filter(p => p.usual_popularity >= 40)
      .sort((a, b) => {
        const sa = a.usual_popularity * Math.max(0, 1 - a.crowd_ratio) - a.wait_time;
        const sb = b.usual_popularity * Math.max(0, 1 - b.crowd_ratio) - b.wait_time;
        return sb - sa;
      })[0] ?? null;
  }

  get zoneRecommendation(): { best: QuadrantData; hot: QuadrantData } | null {
    const places = this.viewPlaces;
    const loc = this.response?.location;
    if (!places?.length || !loc) return null;

    const quads: Record<string, Place[]> = { 'Norte': [], 'Sur': [], 'Este': [], 'Oeste': [] };
    for (const p of places) {
      const dlat = p.lat - loc.lat;
      const dlng = p.lng - loc.lng;
      (Math.abs(dlat) >= Math.abs(dlng)
        ? (dlat >= 0 ? quads['Norte'] : quads['Sur'])
        : (dlng >= 0 ? quads['Este']  : quads['Oeste'])
      ).push(p);
    }

    const quadData: QuadrantData[] = Object.entries(quads)
      .filter(([, ps]) => ps.length >= 2)
      .map(([name, ps]) => ({
        name,
        places: ps,
        avgCrowd:      Math.round(ps.reduce((s, p) => s + p.current_popularity, 0) / ps.length),
        lowCrowdCount: ps.filter(p => !p.is_high_crowd).length,
      }));

    if (quadData.length < 2) return null;
    const best = [...quadData].sort((a, b) => a.avgCrowd - b.avgCrowd)[0];
    const hot  = [...quadData].sort((a, b) => b.avgCrowd - a.avgCrowd)[0];
    return best.name === hot.name ? null : { best, hot };
  }
}

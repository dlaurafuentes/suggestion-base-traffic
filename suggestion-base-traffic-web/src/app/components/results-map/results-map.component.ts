import {
  Component, Input, Output, EventEmitter,
  AfterViewInit, OnChanges, SimpleChanges,
  ElementRef, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { Place, LocationResult } from '../../models/place.model';

@Component({
  selector: 'app-results-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results-map.component.html',
  styleUrls: ['./results-map.component.scss'],
})
export class ResultsMapComponent implements AfterViewInit, OnChanges {
  @Input() places: Place[] = [];
  @Input() center!: LocationResult;
  @Input() radio: number = 2000;
  @Input() selectedPlace: Place | null = null;
  @Output() placeSelected    = new EventEmitter<Place>();
  @Output() geofenceDrawn    = new EventEmitter<[number, number][] | null>();

  @ViewChild('mapContainer', { static: true }) mapRef!: ElementRef<HTMLDivElement>;

  private map!: L.Map;
  private markers: L.Marker[] = [];
  private radiusCircle: L.Circle | null = null;
  private prevPlaceIds: string[] = [];

  // ── Drawing state ────────────────────────────────────────────────
  drawingMode  = false;
  drawPoints: L.LatLng[] = [];
  hasGeofence  = false;

  private drawMarkers:  L.CircleMarker[]  = [];
  private drawPolyline: L.Polyline | null = null;
  private drawPolygon:  L.Polygon  | null = null;

  // ── Lifecycle ────────────────────────────────────────────────────

  ngAfterViewInit() {
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.map) return;
    if (changes['places']) {
      this.renderMarkers();
    }
    if (changes['center'] && this.center) {
      this.map.setView([this.center.lat, this.center.lng], 14);
      this.drawRadiusCircle();
    }
    if (changes['radio'] && this.center) {
      this.drawRadiusCircle();
    }
    if (changes['selectedPlace'] && this.selectedPlace) {
      this.focusPlace(this.selectedPlace);
    }
  }

  // ── Map init ─────────────────────────────────────────────────────

  private initMap() {
    const lat = this.center?.lat ?? 19.43;
    const lng = this.center?.lng ?? -99.13;

    this.map = L.map(this.mapRef.nativeElement, { zoomControl: true }).setView([lat, lng], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(this.map);

    this.map.on('click', (e: L.LeafletMouseEvent) => {
      if (this.drawingMode) this.addDrawPoint(e.latlng);
    });

    if (this.places.length) this.renderMarkers();
    if (this.center)        this.drawRadiusCircle();
  }

  // ── Markers ──────────────────────────────────────────────────────

  private renderMarkers() {
    const newIds = this.places.map(p => p.id);
    const idsChanged = newIds.join(',') !== this.prevPlaceIds.join(',');

    // Update popup content on existing markers when only popularity changed
    if (!idsChanged && this.markers.length === this.places.length) {
      this.places.forEach((place, i) => {
        this.markers[i].setPopupContent(this.buildPopup(place));
        const el = this.markers[i].getElement()?.querySelector('span');
        if (el) {
          el.textContent = `${place.current_popularity}%`;
          const colour = this.crowdColour(place.current_popularity);
          const pin = this.markers[i].getElement()?.querySelector('div') as HTMLElement | null;
          if (pin) pin.style.background = colour;
        }
      });
      return;
    }

    this.prevPlaceIds = newIds;
    this.markers.forEach(m => m.remove());
    this.markers = [];

    for (const place of this.places) {
      const colour = this.crowdColour(place.current_popularity);

      const icon = L.divIcon({
        className: '',
        iconSize:    [40, 40],
        iconAnchor:  [20, 40],
        popupAnchor: [0, -44],
        html: `
          <div style="
            width:40px;height:40px;border-radius:50% 50% 50% 0;
            background:${colour};transform:rotate(-45deg);
            border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.35);
            display:flex;align-items:center;justify-content:center;">
            <span style="transform:rotate(45deg);color:#fff;font-size:.7rem;font-weight:700">
              ${place.current_popularity}%
            </span>
          </div>`,
      });

      const marker = L.marker([place.lat, place.lng], { icon })
        .addTo(this.map)
        .bindPopup(this.buildPopup(place), { maxWidth: 240 });

      marker.on('click', () => this.placeSelected.emit(place));
      this.markers.push(marker);
    }

    if (this.markers.length) {
      const group = L.featureGroup(this.markers);
      this.map.fitBounds(group.getBounds().pad(0.15));
    }
  }

  private drawRadiusCircle() {
    if (this.radiusCircle) { this.radiusCircle.remove(); this.radiusCircle = null; }
    if (!this.center || this.hasGeofence) return;
    this.radiusCircle = L.circle([this.center.lat, this.center.lng], {
      radius:      this.radio,
      color:       '#4361ee',
      weight:      2,
      opacity:     0.7,
      fillColor:   '#4361ee',
      fillOpacity: 0.07,
    }).addTo(this.map);
  }

  private focusPlace(place: Place) {
    this.map.setView([place.lat, place.lng], 16);
  }

  // ── Geofence drawing ─────────────────────────────────────────────

  startDrawing() {
    this.clearGeofence();
    this.drawingMode = true;
    this.drawPoints  = [];
    this.map.getContainer().style.cursor = 'crosshair';
    this.map.doubleClickZoom.disable();
    // Hide radius circle while drawing
    if (this.radiusCircle) { this.radiusCircle.remove(); this.radiusCircle = null; }
  }

  addDrawPoint(latlng: L.LatLng) {
    this.drawPoints.push(latlng);

    const m = L.circleMarker(latlng, {
      radius: 5, color: '#4361ee', fillColor: '#4361ee', fillOpacity: 1, weight: 2,
    }).addTo(this.map);
    this.drawMarkers.push(m);

    if (this.drawPolyline) this.drawPolyline.remove();
    if (this.drawPoints.length >= 2) {
      this.drawPolyline = L.polyline([...this.drawPoints, this.drawPoints[0]], {
        color: '#4361ee', dashArray: '6 4', weight: 2, opacity: 0.8,
      }).addTo(this.map);
    }
  }

  completeDrawing() {
    if (this.drawPoints.length < 3) return;
    this.drawingMode = false;
    this.map.getContainer().style.cursor = '';
    this.map.doubleClickZoom.enable();

    this.drawMarkers.forEach(m => m.remove());
    this.drawMarkers = [];
    if (this.drawPolyline) { this.drawPolyline.remove(); this.drawPolyline = null; }

    this.drawPolygon = L.polygon(this.drawPoints, {
      color: '#4361ee', fillColor: '#4361ee', fillOpacity: 0.12, weight: 2,
    }).addTo(this.map);

    this.hasGeofence = true;
    this.geofenceDrawn.emit(this.drawPoints.map(p => [p.lat, p.lng] as [number, number]));
  }

  cancelDrawing() {
    this.drawingMode = false;
    this.map.getContainer().style.cursor = '';
    this.map.doubleClickZoom.enable();
    this.drawPoints = [];
    this.drawMarkers.forEach(m => m.remove());
    this.drawMarkers = [];
    if (this.drawPolyline) { this.drawPolyline.remove(); this.drawPolyline = null; }
    this.drawRadiusCircle();
  }

  clearGeofence() {
    this.hasGeofence = false;
    this.drawPoints  = [];
    this.drawMarkers.forEach(m => m.remove());
    this.drawMarkers = [];
    if (this.drawPolyline) { this.drawPolyline.remove(); this.drawPolyline = null; }
    if (this.drawPolygon)  { this.drawPolygon.remove();  this.drawPolygon  = null; }
    this.drawRadiusCircle();
    this.geofenceDrawn.emit(null);
  }

  // ── Helpers ──────────────────────────────────────────────────────

  private crowdColour(v: number): string {
    if (v > 66) return '#ef233c';
    if (v > 33) return '#f4a261';
    return '#2a9d8f';
  }

  private buildPopup(p: Place): string {
    const colour = this.crowdColour(p.current_popularity);
    const change = p.crowd_change >= 0 ? `▲ +${p.crowd_change}%` : `▼ ${p.crowd_change}%`;
    const changeColor = p.crowd_change > 0 ? '#ef233c' : '#2a9d8f';
    return `
      <div style="font-family:system-ui;font-size:.85rem;min-width:180px">
        <strong style="font-size:.95rem">${p.name}</strong><br>
        <span style="color:#888">${p.address || '—'}</span><br><br>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="
            background:${colour};color:#fff;padding:.2rem .6rem;
            border-radius:12px;font-weight:700;font-size:.85rem">
            ${p.current_popularity}% actual
          </span>
          <span style="color:${changeColor};font-weight:600">${change}</span>
        </div>
        <div style="margin-top:.5rem;color:#888;font-size:.78rem">
          Habitual: ${p.usual_popularity}% · Ratio: ×${p.crowd_ratio}
        </div>
      </div>`;
  }
}

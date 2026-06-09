import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { SearchRequest, SearchResponse, GiroType, DayPopularity, Place } from '../models/place.model';

@Injectable({ providedIn: 'root' })
export class PlacesService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getGiros(): Observable<GiroType[]> {
    return this.http.get<GiroType[]>(`${this.base}/giros`);
  }

  search(req: SearchRequest): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${this.base}/search`, req);
  }

  getPopularTimes(placeId: string, giro: string): Observable<{ popular_times: DayPopularity[] }> {
    return this.http.get<{ popular_times: DayPopularity[] }>(
      `${this.base}/places/${encodeURIComponent(placeId)}/popular-times`,
      { params: { giro } },
    );
  }

  getCrowd(placeId: string, giro: string): Observable<Partial<Place>> {
    return this.http.get<Partial<Place>>(
      `${this.base}/places/${encodeURIComponent(placeId)}/crowd`,
      { params: { giro } },
    );
  }
}

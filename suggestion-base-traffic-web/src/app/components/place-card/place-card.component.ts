import {
  Component, Input, Output, EventEmitter, AfterViewInit, ElementRef, inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Place } from '../../models/place.model';

@Component({
  selector: 'app-place-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './place-card.component.html',
  styleUrls: ['./place-card.component.scss'],
})
export class PlaceCardComponent implements AfterViewInit {
  private el = inject(ElementRef);
  @Input() place!: Place;
  @Input() selected = false;
  @Output() cardClicked = new EventEmitter<Place>();

  ngAfterViewInit() {
    const bs = (window as any).bootstrap;
    if (bs?.Tooltip) {
      this.el.nativeElement
        .querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach((el: Element) => new bs.Tooltip(el, { trigger: 'hover', delay: { show: 400, hide: 0 } }));
    }
  }

  get crowdClass(): string {
    if (this.place.current_popularity > 66) return 'high';
    if (this.place.current_popularity > 33) return 'medium';
    return 'low';
  }

  get crowdLabel(): string {
    if (this.place.current_popularity > 66) return 'Alta afluencia';
    if (this.place.current_popularity > 33) return 'Afluencia moderada';
    return 'Poca afluencia';
  }

  get changeIcon(): string {
    if (this.place.crowd_change > 10) return 'bi-arrow-up-circle-fill text-danger';
    if (this.place.crowd_change < -10) return 'bi-arrow-down-circle-fill text-success';
    return 'bi-dash-circle-fill text-secondary';
  }

  get changeText(): string {
    const v = this.place.crowd_change;
    return v >= 0 ? `+${v}%` : `${v}%`;
  }
}

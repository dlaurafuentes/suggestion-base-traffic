import {
  Component, Input, OnChanges, SimpleChanges,
  AfterViewInit, ViewChild, ElementRef, OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, registerables } from 'chart.js';
import { Place, DayPopularity } from '../../models/place.model';

Chart.register(...registerables);

@Component({
  selector: 'app-crowd-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './crowd-chart.component.html',
  styleUrls: ['./crowd-chart.component.scss'],
})
export class CrowdChartComponent implements AfterViewInit, OnChanges {
  @Input() place!: Place;
  @Input() highlightHour: number | null = null;

  @ViewChild('chartCanvas') chartRef!: ElementRef<HTMLCanvasElement>;

  private chart: Chart | null = null;
  selectedDay = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1; // 0=Mon…6=Sun
  currentHour = new Date().getHours();

  readonly dayNames = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  readonly hourLabels = Array.from({ length: 24 }, (_, i) => {
    const h = i % 12 || 12;
    return `${h}${i < 12 ? 'am' : 'pm'}`;
  });

  get currentDay(): DayPopularity | undefined {
    return this.place?.popular_times?.[this.selectedDay];
  }

  get crowdLabel(): string {
    const v = this.place?.current_popularity ?? 0;
    if (v > 66) return 'Alta';
    if (v > 33) return 'Moderada';
    return 'Baja';
  }

  get crowdColor(): string {
    const v = this.place?.current_popularity ?? 0;
    if (v > 66) return '#ef233c';
    if (v > 33) return '#f4a261';
    return '#2a9d8f';
  }

  ngAfterViewInit() {
    this.buildChart();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.chart) return;
    if (changes['place'] || changes['highlightHour']) {
      this.updateChart();
    }
  }

  selectDay(idx: number) {
    this.selectedDay = idx;
    this.updateChart();
  }

  private barColours(data: number[]): string[] {
    const todayIdx = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
    const active = this.highlightHour !== null
      ? this.highlightHour
      : (this.selectedDay === todayIdx ? this.currentHour : -1);
    return data.map((_, i) => i === active ? '#ef233c' : 'rgba(67,97,238,.55)');
  }

  private buildChart() {
    if (!this.chartRef || !this.place) return;
    const ctx = this.chartRef.nativeElement.getContext('2d')!;
    const day = this.currentDay;
    if (!day) return;

    this.chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: this.hourLabels,
        datasets: [{
          label: 'Habitual',
          data: day.data,
          backgroundColor: this.barColours(day.data),
          borderRadius: 3,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: { label: ctx => ` ${ctx.parsed.y}% de ocupación` },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 0 } },
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: v => `${v}%` },
            grid: { color: 'rgba(0,0,0,.06)' },
          },
        },
      },
    });
  }

  private updateChart() {
    if (!this.chart || !this.place) return;
    const day = this.currentDay;
    if (!day) return;

    this.chart.data.datasets[0].data = day.data;
    (this.chart.data.datasets[0].backgroundColor as string[]) = this.barColours(day.data);
    this.chart.update('none');
  }
}

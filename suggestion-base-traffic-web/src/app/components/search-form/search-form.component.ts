import {
  Component, OnInit, OnDestroy, Output, EventEmitter, inject, ElementRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule, FormsModule, FormBuilder, FormGroup, AbstractControl,
} from '@angular/forms';
import { PlacesService } from '../../services/places.service';
import { GiroType, SearchRequest } from '../../models/place.model';

@Component({
  selector: 'app-search-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './search-form.component.html',
  styleUrls: ['./search-form.component.scss'],
})
export class SearchFormComponent implements OnInit, OnDestroy {
  @Output() searchSubmitted = new EventEmitter<SearchRequest>();

  private fb  = inject(FormBuilder);
  private svc = inject(PlacesService);
  private el  = inject(ElementRef);

  form!: FormGroup;
  giros: GiroType[] = [];
  giroCategories: string[] = [];
  girosByCategory: Record<string, GiroType[]> = {};

  selectedGiros: string[] = [];
  dropdownOpen = false;
  giroSearch = '';

  readonly estados = [
    'Aguascalientes','Baja California','Baja California Sur','Campeche',
    'Chiapas','Chihuahua','Ciudad de México','Coahuila','Colima','Durango',
    'Guanajuato','Guerrero','Hidalgo','Jalisco','Estado de México',
    'Michoacán','Morelos','Nayarit','Nuevo León','Oaxaca','Puebla',
    'Querétaro','Quintana Roo','San Luis Potosí','Sinaloa','Sonora',
    'Tabasco','Tamaulipas','Tlaxcala','Veracruz','Yucatán','Zacatecas',
  ];

  readonly radioOptions = [
    { value: 500,   label: '500 m'  },
    { value: 1000,  label: '1 km'   },
    { value: 2000,  label: '2 km'   },
    { value: 3000,  label: '3 km'   },
    { value: 5000,  label: '5 km'   },
    { value: 10000, label: '10 km'  },
    { value: 20000, label: '20 km'  },
  ];

  private readonly onDocClick = (e: Event) => {
    if (!this.el.nativeElement.contains(e.target as Node)) {
      this.dropdownOpen = false;
    }
  };

  ngOnInit() {
    this.form = this.fb.group({
      giros:  [[] as string[], [(c: AbstractControl) => (c.value?.length ? null : { required: true })]],
      estado: ['',             [(c: AbstractControl) => (c.value ? null : { required: true })]],
      ciudad: [''],
      radio:  [2000],
    });

    document.addEventListener('click', this.onDocClick);

    this.svc.getGiros().subscribe({
      next: (data) => {
        this.giros = data;
        this.girosByCategory = {};
        for (const g of data) {
          if (!this.girosByCategory[g.category]) this.girosByCategory[g.category] = [];
          this.girosByCategory[g.category].push(g);
        }
        this.giroCategories = Object.keys(this.girosByCategory);
      },
    });
  }

  ngOnDestroy() {
    document.removeEventListener('click', this.onDocClick);
  }

  // ── Multiselect helpers ──────────────────────────────────────

  getGiroMeta(value: string): GiroType {
    return this.giros.find(g => g.value === value)
      ?? { value, label: value, icon: '', category: '' };
  }

  isGiroSelected(value: string): boolean {
    return this.selectedGiros.includes(value);
  }

  isCategoryAllSelected(cat: string): boolean {
    return (this.girosByCategory[cat] ?? []).every(g => this.isGiroSelected(g.value));
  }

  isCategoryPartialSelected(cat: string): boolean {
    const n = (this.girosByCategory[cat] ?? []).filter(g => this.isGiroSelected(g.value)).length;
    return n > 0 && n < (this.girosByCategory[cat] ?? []).length;
  }

  toggleGiro(value: string) {
    const idx = this.selectedGiros.indexOf(value);
    if (idx >= 0) this.selectedGiros.splice(idx, 1);
    else this.selectedGiros.push(value);
    this.form.get('giros')!.setValue([...this.selectedGiros]);
    this.form.get('giros')!.markAsTouched();
  }

  toggleCategory(cat: string) {
    const vals = (this.girosByCategory[cat] ?? []).map(g => g.value);
    if (this.isCategoryAllSelected(cat)) {
      this.selectedGiros = this.selectedGiros.filter(v => !vals.includes(v));
    } else {
      for (const v of vals) {
        if (!this.selectedGiros.includes(v)) this.selectedGiros.push(v);
      }
    }
    this.form.get('giros')!.setValue([...this.selectedGiros]);
    this.form.get('giros')!.markAsTouched();
  }

  removeGiro(value: string, event: Event) {
    event.stopPropagation();
    this.selectedGiros = this.selectedGiros.filter(v => v !== value);
    this.form.get('giros')!.setValue([...this.selectedGiros]);
  }

  get filteredCategories(): string[] {
    if (!this.giroSearch.trim()) return this.giroCategories;
    const q = this.giroSearch.toLowerCase();
    return this.giroCategories.filter(cat =>
      (this.girosByCategory[cat] ?? []).some(g => g.label.toLowerCase().includes(q))
    );
  }

  filteredGirosByCategory(cat: string): GiroType[] {
    const all = this.girosByCategory[cat] ?? [];
    if (!this.giroSearch.trim()) return all;
    const q = this.giroSearch.toLowerCase();
    return all.filter(g => g.label.toLowerCase().includes(q));
  }

  catCount(cat: string): string {
    const giros = this.filteredGirosByCategory(cat);
    if (!giros.length) return '';
    const sel = giros.filter(g => this.isGiroSelected(g.value)).length;
    return `${sel}/${giros.length}`;
  }

  // ── Form submit ──────────────────────────────────────────────

  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { giros, estado, ciudad, radio } = this.form.value;
    this.searchSubmitted.emit({
      giros,
      estado,
      ciudad: ciudad || undefined,
      radio:  radio ?? 2000,
    });
  }

  isInvalid(field: string): boolean {
    const ctrl = this.form.get(field);
    return !!(ctrl?.invalid && ctrl.touched);
  }
}

import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, OnDestroy } from '@angular/core';

@Component({
  selector: 'app-image-result',
  standalone: true,
  templateUrl: './image-result.component.html',
  styleUrls: ['./image-result.component.css']
})
export class ImageResultComponent implements OnChanges, OnDestroy {
  @Input() imageUrl: string | null = null;
  @Input() originalImageUrl: string | null = null;
  @Input() isLoading: boolean = false;

  @Output() openFullView = new EventEmitter<void>();

  sliderPosition = 50;
  progressValue = 0;
  private progressInterval: ReturnType<typeof setInterval> | null = null;
  readonly CIRCUMFERENCE = 2 * Math.PI * 40;

  ngOnChanges(changes: SimpleChanges) {
    if (changes['isLoading']) {
      this.isLoading ? this.startProgress() : this.finishProgress();
    }
  }

  ngOnDestroy() { this.clearInterval(); }

  private startProgress() {
    this.progressValue = 0;
    this.clearInterval();
    this.progressInterval = setInterval(() => {
      if (this.progressValue < 25)      this.progressValue = Math.min(this.progressValue + 4, 25);
      else if (this.progressValue < 65) this.progressValue = Math.min(this.progressValue + 1.5, 65);
      else if (this.progressValue < 88) this.progressValue = Math.min(this.progressValue + 0.35, 88);
    }, 60);
  }

  private finishProgress() {
    this.clearInterval();
    this.progressValue = 100;
  }

  private clearInterval() {
    if (this.progressInterval !== null) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
    }
  }

  get dashOffset(): number { return this.CIRCUMFERENCE * (1 - this.progressValue / 100); }
  get progressDisplay(): number { return Math.floor(this.progressValue); }

  updateSlider(event: Event) {
    this.sliderPosition = Number((event.target as HTMLInputElement).value);
  }

  requestFullView() {
    this.openFullView.emit();
  }
}

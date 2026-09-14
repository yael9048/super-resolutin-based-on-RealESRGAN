import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-image-upload',
  standalone: true,
  templateUrl: './image-upload.component.html',
  styleUrls: ['./image-upload.component.css']
})
export class ImageUploadComponent {
  @Input() imageUrl: string | null = null;
  @Output() fileSelected = new EventEmitter<File>();

  isDragging = false;
  rippleX = 0;
  rippleY = 0;
  rippleActive = false;
  private rippleTimeout: ReturnType<typeof setTimeout> | null = null;

  onFileChange(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.fileSelected.emit(file);
  }

  triggerRipple(event: MouseEvent) {
    const el = event.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    this.rippleX = event.clientX - rect.left;
    this.rippleY = event.clientY - rect.top;
    if (this.rippleTimeout) clearTimeout(this.rippleTimeout);
    this.rippleActive = false;
    setTimeout(() => {
      this.rippleActive = true;
      this.rippleTimeout = setTimeout(() => { this.rippleActive = false; }, 750);
    }, 0);
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragEnter(event: DragEvent) {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    const file = event.dataTransfer?.files[0];
    if (file && file.type.startsWith('image/')) {
      this.fileSelected.emit(file);
    }
  }
}

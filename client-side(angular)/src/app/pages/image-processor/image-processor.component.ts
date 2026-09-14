import { Component, inject, ChangeDetectorRef, OnInit, HostListener } from '@angular/core';
import { ImageService } from '../../services/image.service';
import { ImageUploadComponent } from '../../components/image-upload/image-upload.component';
import { ImageResultComponent } from '../../components/image-result/image-result.component';

@Component({
  selector: 'app-image-processor',
  standalone: true,
  imports: [ImageUploadComponent, ImageResultComponent],
  templateUrl: './image-processor.component.html',
  styleUrls: ['./image-processor.component.css']
})
export class ImageProcessorComponent implements OnInit {
  private imageService = inject(ImageService);
  private cdr = inject(ChangeDetectorRef);

  originalImageUrl: string | null = null;
  enhancedImageUrl: string | null = null;
  isLoading = false;
  errorMessage: string | null = null;

  // לייטבוקס ברמת הדף
  lightboxOpen = false;
  lbSlider = 50;

  ngOnInit() {
    this.originalImageUrl = this.imageService.currentOriginalUrl;
    this.enhancedImageUrl = this.imageService.currentEnhancedUrl;
    this.isLoading = this.imageService.isProcessing;
  }

  @HostListener('document:keydown.escape')
  onEsc() { this.closeLightbox(); }

  openLightbox() {
    this.lightboxOpen = true;
    this.lbSlider = 50;
  }

  closeLightbox() { this.lightboxOpen = false; }

  updateLbSlider(event: Event) {
    this.lbSlider = Number((event.target as HTMLInputElement).value);
  }

  handleFileSelected(file: File) {
    this.originalImageUrl = URL.createObjectURL(file);
    this.enhancedImageUrl = null;
    this.isLoading = true;
    this.errorMessage = null;

    this.imageService.currentOriginalUrl = this.originalImageUrl;
    this.imageService.currentEnhancedUrl = null;
    this.imageService.isProcessing = true;

    this.cdr.detectChanges();

    const userIdStr = localStorage.getItem('currentUserId');
    const currentUserId = userIdStr ? parseInt(userIdStr, 10) : 1;

    this.imageService.enhanceImage(currentUserId, file).subscribe({
      next: (responseBlob: Blob) => {
        const objectUrl = URL.createObjectURL(responseBlob);
        this.enhancedImageUrl = objectUrl;
        this.isLoading = false;
        this.imageService.currentEnhancedUrl = objectUrl;
        this.imageService.isProcessing = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('שגיאה:', error);
        this.isLoading = false;
        this.imageService.isProcessing = false;

        if (error.status === 0) {
          this.errorMessage = 'לא ניתן להתחבר לשרת. אנא ודאו שהשרת פועל ושיש חיבור לרשת.';
          this.cdr.detectChanges();
        } else if (error.error instanceof Blob) {
          error.error.text().then((text: string) => {
            this.errorMessage = text.includes('Security Alert')
              ? 'הקובץ שהעלאתם אינו תמונה תקינה. אנא נסו להעלות קובץ JPEG או PNG.'
              : 'אירעה שגיאה בשרת: ' + text;
            this.cdr.detectChanges();
          });
        } else {
          this.errorMessage = 'אירעה שגיאה בלתי צפויה. נסו שוב מאוחר יותר.';
          this.cdr.detectChanges();
        }
      }
    });
  }

  closeErrorPopup() {
    this.errorMessage = null;
    this.cdr.detectChanges();
  }
}

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http'; 
import { RouterLink } from '@angular/router'; 
import { ImageService } from '../../services/image.service';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterLink], 
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {
  private imageService = inject(ImageService);
  private http = inject(HttpClient); 

  historyList: any[] = [];
  isLoading = true;
  errorMessage = '';
  isGuest = false; // המשתנה החדש שלנו
  private baseUrl = 'https://localhost:7062/uploads/';

  // --- משתני Lightbox מעודכנים ---
  selectedItem: any = null; 
  selectedImageType: 'original' | 'enhanced' | null = null; 
  selectedImageUrl: string | null = null; 
  selectedFileName: string | null = null; 

  ngOnInit() {
    const userIdStr = localStorage.getItem('currentUserId');
    
    // בודקים אם יש משתמש. אם לא - מציגים את מסך האורח
    if (!userIdStr) {
      this.isGuest = true;
      this.isLoading = false;
      return;
    }
    
    const userId = parseInt(userIdStr, 10);

    this.imageService.getHistory(userId).subscribe({
      next: (data) => {
        this.historyList = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.errorMessage = 'שגיאה בטעינת ההיסטוריה.';
        this.isLoading = false;
      }
    });
  }

  // --- פונקציות מחיקה ---
  deleteHistoryItem(imageId: number) {
    if (!confirm('האם את/ה בטוח/ה שברצונך למחוק תמונה זו לצמיתות?')) return;

    this.imageService.deleteImage(imageId).subscribe({
      next: () => {
        this.historyList = this.historyList.filter(item => item.imageId !== imageId);
      },
      error: (err) => {
        console.error('שגיאה במחיקה:', err);
        alert('שגיאה במחיקת התמונה.');
      }
    });
  }

  // --- פונקציות Lightbox ---
  openLightbox(item: any, type: 'original' | 'enhanced') {
    this.selectedItem = item;
    this.selectedImageType = type;
    this.updateLightboxDisplay();
    document.body.style.overflow = 'hidden'; 
  }

  updateLightboxDisplay() {
    if (this.selectedImageType === 'original') {
      this.selectedImageUrl = this.baseUrl + this.selectedItem.originalUrl;
      this.selectedFileName = 'original_' + this.selectedItem.originalUrl;
    } else {
      this.selectedImageUrl = this.baseUrl + this.selectedItem.enhancedUrl;
      this.selectedFileName = this.selectedItem.enhancedUrl;
    }
  }

  navigateLightbox(direction: 'next' | 'prev') {
    if (direction === 'next' && this.selectedImageType === 'original' && this.selectedItem.status === 'Completed') {
      this.selectedImageType = 'enhanced'; 
      this.updateLightboxDisplay();
    } else if (direction === 'prev' && this.selectedImageType === 'enhanced') {
      this.selectedImageType = 'original'; 
      this.updateLightboxDisplay();
    }
  }

  closeLightbox() {
    this.selectedItem = null;
    this.selectedImageType = null;
    this.selectedImageUrl = null;
    document.body.style.overflow = 'auto'; 
  }

  downloadImage() {
    if (!this.selectedImageUrl || !this.selectedFileName) return;
    this.http.get(this.selectedImageUrl, { responseType: 'blob' }).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.selectedFileName || 'image_ai.jpg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => alert('הורדת הקובץ נכשלה.')
    });
  }
}
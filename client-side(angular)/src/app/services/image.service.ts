import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ImageService {
 //הגדרה קבועה לריצה על פורט 7062
  private apiUrl = 'https://localhost:7062/api/images';

  private http = inject(HttpClient);
//  הזיכרון של האפליקציה 
  currentOriginalUrl: string | null = null;
  currentEnhancedUrl: string | null = null;
  isProcessing = false;

  enhanceImage(userId: number, file: File): Observable<Blob> {
    const formData = new FormData();
    formData.append('image', file, file.name);


    return this.http.post(`${this.apiUrl}/enhance/${userId}`, formData, {
      responseType: 'blob' 
    });
  }

  //  משיכת היסטוריית התמונות של המשתמש
  getHistory(userId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/history/${userId}`);
  }

  // מחיקת תמונה מההיסטוריה (מול השרת)
  deleteImage(imageId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${imageId}`);
  }
}
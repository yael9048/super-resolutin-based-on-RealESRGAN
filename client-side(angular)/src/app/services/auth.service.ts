import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'https://localhost:7062/api/auth';

  private http = inject(HttpClient);

  //  הרשמת משתמש חדש
  
  register(userData: any): Observable<any> {
    // userData צריך להכיל: { username: '...', email: '...', password: '...' }
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  // התחברות משתמש קיים
  login(credentials: any): Observable<any> {
    // credentials צריך להכיל: { email: '...', password: '...' }
    return this.http.post(`${this.apiUrl}/login`, credentials);
  }
}
import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, Router } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive], 
  templateUrl:'./navbar.html',
  styleUrls: ['./navbar.css']
})
export class NavbarComponent {
  private router = inject(Router);

  get isLoggedIn(): boolean {
    return !!localStorage.getItem('currentUserId');
  }

  get currentUsername(): string {
    // אם אין שם משתמש בזיכרון, נציג  'אורח'
    return localStorage.getItem('currentUsername') || 'אורח';
  }

  switchAccount() {
    this.router.navigate(['/login']);
  }

  logout() {
    localStorage.removeItem('currentUserId'); 
    localStorage.removeItem('currentUsername'); 
    this.router.navigate(['/login']); 
  }
}
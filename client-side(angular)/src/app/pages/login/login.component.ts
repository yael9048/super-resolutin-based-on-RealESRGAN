import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm: FormGroup;
  serverError: string | null = null;
  isLoading = false;

  private authService = inject(AuthService);
  private router = inject(Router);

  constructor(private fb: FormBuilder) {
    this.loginForm = this.fb.group({
      email:    ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit() {
    this.serverError = null;
    if (this.loginForm.valid) {
      this.isLoading = true;
      this.authService.login(this.loginForm.value).subscribe({
        next: (response: any) => {
          this.isLoading = false;
          localStorage.setItem('currentUserId',   response.userId);
          localStorage.setItem('currentUsername', response.username);
          this.router.navigate(['/app']);
        },
        error: (error) => {
          this.isLoading = false;
          this.serverError = error.error?.message || 'שגיאה בתקשורת עם השרת. נסו שוב.';
        }
      });
    } else {
      this.loginForm.markAllAsTouched();
    }
  }
}

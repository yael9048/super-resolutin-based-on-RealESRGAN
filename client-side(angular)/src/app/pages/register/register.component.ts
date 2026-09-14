import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';

export function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
  const password        = control.get('password');
  const confirmPassword = control.get('confirmPassword');

  if (password && confirmPassword && password.value !== confirmPassword.value) {
    confirmPassword.setErrors({ ...confirmPassword.errors, passwordMismatch: true });
    return { passwordMismatch: true };
  } else if (confirmPassword?.hasError('passwordMismatch')) {
    const current = { ...confirmPassword.errors };
    delete current['passwordMismatch'];
    confirmPassword.setErrors(Object.keys(current).length > 0 ? current : null);
  }
  return null;
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  registerForm: FormGroup;
  isLoading = false;
  serverError:   string | null = null;
  serverSuccess: string | null = null;

  showPassword        = false;
  showConfirmPassword = false;

  private authService = inject(AuthService);
  private router      = inject(Router);

  constructor(private fb: FormBuilder) {
    this.registerForm = this.fb.group({
      username:        ['', Validators.required],
      email:           ['', [Validators.required, Validators.email]],
      password:        ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', Validators.required]
    }, { validators: passwordMatchValidator });
  }

  togglePasswordVisibility()        { this.showPassword        = !this.showPassword; }
  toggleConfirmPasswordVisibility() { this.showConfirmPassword = !this.showConfirmPassword; }

  onSubmit() {
    this.serverError   = null;
    this.serverSuccess = null;

    if (this.registerForm.valid) {
      this.isLoading = true;
      const data = {
        username: this.registerForm.value.username,
        email:    this.registerForm.value.email,
        password: this.registerForm.value.password
      };

      this.authService.register(data).subscribe({
        next: (response: any) => {
          this.isLoading = false;
          // שמירת פרטי המשתמש — זהה להתחברות רגילה
          if (response.userId)   localStorage.setItem('currentUserId',   response.userId);
          if (response.username) localStorage.setItem('currentUsername', response.username);
          this.serverSuccess = response.message || 'ההרשמה בוצעה בהצלחה!';
          setTimeout(() => this.router.navigate(['/app']), 2200);
        },
        error: (error) => {
          this.isLoading = false;
          this.serverError = error.error?.message || 'שגיאה בתקשורת עם השרת. נסו שוב.';
        }
      });
    } else {
      this.registerForm.markAllAsTouched();
    }
  }
}

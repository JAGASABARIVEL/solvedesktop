import { Component } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { PasswordModule } from 'primeng/password';
import { InputTextModule } from 'primeng/inputtext';
import { FloatLabelModule } from 'primeng/floatlabel';
import { DividerModule } from 'primeng/divider';
import { AuthService } from '../../shared/services/auth/auth.service';
import { LayoutService } from '../../layout/service/app.layout.service';
import { Router } from '@angular/router';
import { SkeletonModule } from 'primeng/skeleton';
import { LoginModel, LoginResponseModel } from './login.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ButtonModule,
    CheckboxModule,
    InputTextModule,
    PasswordModule,
    FloatLabelModule,
    DividerModule,
    SkeletonModule
    
  ],
  templateUrl: './login.component.html',
  styles: [`
      :host ::ng-deep .pi-eye,
      :host ::ng-deep .pi-eye-slash {
          transform:scale(1.6);
          margin-right: 1rem;
          color: var(--primary-color) !important;
      }
  `]
})
export class LoginComponent {
  valCheck: string[] = ['remember'];
  formGroup!: FormGroup;
  loading = false;
  login_payload: LoginModel = undefined;

    constructor(
        private router: Router,
        private formBuilder: FormBuilder,
        private authService: AuthService,
        public layoutService: LayoutService
    ) {
        this.formGroup = this.formBuilder.group({
            user_phone: ['', [Validators.required]],
            user_password: ['', [Validators.required, Validators.minLength(4)]]
        });
     }

     saveUserDetails(loginDetais: LoginResponseModel) {
        localStorage.setItem('me', JSON.stringify(loginDetais));
     }

    loginButton() {
        this.loading = true;
        this.login_payload = {
            "phone" : this.formGroup.value.user_phone,
            "password" : this.formGroup.value.user_password
        }

        this.authService.login(this.login_payload).subscribe(
            (res: LoginResponseModel) => {
                this.saveUserDetails(res);
                
                this.loading = false;
                this.router.navigate(['schedule']);
            },
            (err) => {
                this.loading = false;
                console.log(err);
            }
        )
    }

    navigateToSignUp() {
        this.router.navigate(["signup"])
    }
}
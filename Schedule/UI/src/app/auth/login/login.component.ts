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
import { AvatarModule } from 'primeng/avatar';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

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
    SkeletonModule,
    AvatarModule,
    ToastModule
  ],
  providers: [
    MessageService
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
        private messageService: MessageService,
        private authService: AuthService,
        public layoutService: LayoutService,
    ) {
        this.formGroup = this.formBuilder.group({
            user_phone: ['', [Validators.required]],
            user_password: ['', [Validators.required, Validators.minLength(4)]],
            uuid: ['', [Validators.required]]
        });
     }

     saveUserDetails(loginDetais: LoginResponseModel) {
        localStorage.setItem('me', JSON.stringify(loginDetais));
     }

    loginButton() {
        this.loading = true;
        this.login_payload = {
            "phone" : this.formGroup.value.user_phone,
            "password" : this.formGroup.value.user_password,
            "uuid": this.formGroup.value.uuid
        }

        this.authService.login(this.login_payload).subscribe(
            (res: LoginResponseModel) => {
                this.saveUserDetails(res);
                this.loading = false;
                this.router.navigate(['']);
            },
            (err) => {
                this.loading = false;
                let error_details = err.error?.error ? err.error.error : err.message;
                this.messageService.add({ severity: 'error', summary: 'Login Failure', detail: error_details, sticky: true });
            }
        )
    }

    navigateToSignUp() {
        this.router.navigate(["signup"])
    }
}

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { SelectButtonChangeEvent, SelectButtonModule } from 'primeng/selectbutton';
import { DropdownModule } from 'primeng/dropdown';
import { SkeletonModule } from 'primeng/skeleton';

import { LayoutService } from '../../layout/service/app.layout.service';
import { AuthService } from '../../shared/services/auth/auth.service';
import { Router } from '@angular/router';
import { EmployeeSignup, OwnerSignup } from './signup.models';
import { AvatarModule } from 'primeng/avatar';
import { OrganizationService } from '../../shared/services/Organization/organization.service';
import { supported_platforms } from '../../shared/services/constants';

@Component({
  selector: 'app-signup',
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
    SelectButtonModule,
    DropdownModule,
    SkeletonModule,
    AvatarModule,
  ],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.css'
})
export class SignupComponent implements OnInit {
  roles!: any;
  role_selected!: string;
  organization!: any;
  selectedOrganization!: any;
  formGroup!: FormGroup;
  loading: boolean = false;
  platforms = supported_platforms;
  selected_platform: any = undefined;
  owner_signup_payload: OwnerSignup = undefined;
  employee_signup_payload: EmployeeSignup = undefined;


  constructor(
    private router: Router,
    private formBuilder: FormBuilder,
    private authService: AuthService,
    public layoutService: LayoutService,
    private organizationService: OrganizationService
) {
    this.formGroup = this.formBuilder.group({
        user_name: ['', [Validators.required]],
        user_phone: ['', [Validators.required]],
        user_email: ['', [Validators.required, Validators.email]],
        user_role: ['', [Validators.required]],
        user_organization: ['', [Validators.required]],
        user_platform: [''],
        user_platform_key: [''],
        user_login_id: [''],
        user_password: ['', [Validators.required, Validators.minLength(8)]],
        user_confirm_password: ['', [Validators.required]]
    },
    {
      validators: [this.passwordMatchValidator] // Attach the cross-field validator here
    }
    );
 }

 passwordMatchValidator(formGroup: FormGroup): null {
  const password = formGroup.get('user_password');
  const confirmPassword = formGroup.get('user_confirm_password');
  if (password && confirmPassword) {
    if (password.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true }); // Set error on the specific control
    } else {
      confirmPassword.setErrors(null); // Clear any existing errors
    }
  }
  return null; // No need to return errors at the form level
}
  ngOnInit(): void {
    this.roles = [
      {label: 'Employee', value: 'employee'},
      {label: 'Owner', value: 'owner'},
    ]
    this.loadOrganization();
  }

  loadOrganization() {
    this.organizationService.fetch_all_organizations().subscribe(
      (res) => {
        this.organization = res;
      },
      (err) => {
        console.log("Signup | Can not load organizations", err);
      }
    )
  }

  onRoleSelect(event: SelectButtonChangeEvent) {
    this.role_selected = event.value;
  }

  // Custom validator to ensure passwords match


signupButton() {
    let payload = undefined;
    this.loading = true;
    if (this.role_selected == "owner") {
      this.owner_signup_payload = {
        "name": this.formGroup.value.user_name,
        "phone": this.formGroup.value.user_phone,
        "email": this.formGroup.value.user_email,
        "user_type": this.formGroup.value.user_role,
        "organization": this.formGroup.value.user_organization,
        "platform_name": this.formGroup.value.user_platform.name,
        "login_id": this.formGroup.value.user_login_id,
        "platform_login_credentials": this.formGroup.value.user_platform_key,
        "password": this.formGroup.value.user_password
      }
      payload = this.owner_signup_payload;
    }
    else if(this.role_selected == "employee") {
      this.employee_signup_payload = {
        "name": this.formGroup.value.user_name,
        "phone": this.formGroup.value.user_phone,
        "email": this.formGroup.value.user_email,
        "user_type": this.formGroup.value.user_role,
        "organization": this.formGroup.value.user_organization?.name,
        "password": this.formGroup.value.user_password
      }
      payload = this.employee_signup_payload;
    }
    this.authService.signup(payload).subscribe(
      (res) => {
        this.loading = false;
        this.router.navigate(["login"])
      },
      (err) => {
        this.loading = false;
        console.log(err);
      }
    );
    console.log("Typed signup form is ", this.formGroup.value);
    
}
navigateToLogin() {
  this.router.navigate(["login"])
}

}

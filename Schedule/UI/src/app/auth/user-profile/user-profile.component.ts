import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { DividerModule } from 'primeng/divider';
import { DropdownModule } from 'primeng/dropdown';
import { LoginResponseModel } from '../login/login.model';
import { Router } from '@angular/router';


@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputTextModule,
    DialogModule,
    DividerModule,
    DropdownModule
  ],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.scss'
})
export class UserProfileComponent implements OnInit {

  supported_platforms = [
    {"name": "Whatsapp"}
  ]
  selected_platform : any = undefined;

  user: LoginResponseModel = undefined;
  platforms = [
    {
      name: "Whatsapp",
      token: "sdjfhbsdjknklj"
    },
  ]

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.user = JSON.parse(localStorage.getItem('me'));
    if (!this.user) {
      this.router.navigate(['login']);
    }
  }
 


  

  updateProfile() {
    // Handle profile update logic
    console.log('Profile updated:', this.user);
  }

  visible: boolean = false;

  showDialog() {
      this.visible = true;
  }

  onPlatformSelected() {

  }
}

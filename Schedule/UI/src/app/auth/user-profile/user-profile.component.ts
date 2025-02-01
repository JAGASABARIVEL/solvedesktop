import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { DividerModule } from 'primeng/divider';
import { DropdownModule } from 'primeng/dropdown';
import { LoginResponseModel } from '../login/login.model';
import { Router } from '@angular/router';
import { PlatformService } from '../../shared/services/Platform/platform.service';
import { PlatformModel } from '../../shared/services/Platform/platform.model';
import { ToastModule } from 'primeng/toast';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { OrganizationService } from '../../shared/services/Organization/organization.service';



@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ButtonModule,
    InputTextModule,
    DialogModule,
    DividerModule,
    DropdownModule,
    ToastModule,
    InputGroupModule,
    InputGroupAddonModule
  ],
  providers: [
    MessageService
  ],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.scss'
})
export class UserProfileComponent implements OnInit {

  supported_platforms = [
    {"name": "Whatsapp"}
  ]
  selected_platform : any = undefined;
  formGroup!: FormGroup;

  user: LoginResponseModel = undefined;
  org_name!: string;
  platforms!: PlatformModel[];
  new_platform!: PlatformModel;

  constructor(
    private router: Router,
    private platforService: PlatformService,
    private messageService: MessageService,
    private formBuilder: FormBuilder,
    private organizationService: OrganizationService
  ) {
        this.formGroup = this.formBuilder.group({
          selected_platform_ctrl: ['', [Validators.required]],
          login_id_form_filed_ctrl: ['', [Validators.required]],
          token_form_filed_ctrl: ['', [Validators.required]]
        });
  }

  ngOnInit(): void {
    this.user = JSON.parse(localStorage.getItem('me'));
    if (!this.user) {
      this.router.navigate(['login']);
    }
    this.loadRegisteredPlatforms();
    this.new_platform = {
      id: undefined,
      platform_name: undefined,
      token: undefined,
      login_id: undefined,
      owner_id: this.user.id,
      status: 'active'
    }

    this.organizationService.fetch_name(this.user.organization).subscribe((data) => {
      this.org_name = data.name;
    },
    (err) => {
      console.log("List conversation | Error getting users ", err);
    }
    );
  }

  loadRegisteredPlatforms() {
    this.platforService.getPlatforms({"organization_id": this.user.organization}).subscribe(
      (data) => {
        this.platforms = data;
        console.log("this.platforms ", this.platforms);
      },
      (err) => {
        console.log("Compose Message | Error getting platforms ", err);  
      }
    );
  }

  updateProfile() {
    // Handle profile update logic
    console.log('Profile updated:', this.user);
  }

  visible: boolean = false;

  showDialog() {
      this.visible = true;
  }

  resetPlatform() {
    this.selected_platform = null;
    this.new_platform = {
      id: undefined,
      platform_name: undefined,
      token: undefined,
      login_id: undefined,
      owner_id: this.user.id,
      status: 'active'     
    }
  }

  onAddPlatform() {
    this.new_platform.owner_id = this.user.id;
    console.log("Selected Platform name ", this.new_platform.platform_name);

    
    
    this.new_platform.platform_name = this.formGroup.value.selected_platform_ctrl.name.toLowerCase() + '_' + this.platforms.length;
    this.new_platform.login_id = this.formGroup.value.login_id_form_filed_ctrl
    this.new_platform.token = this.formGroup.value.token_form_filed_ctrl
    this.new_platform.status = 'active';
    this.platforService.createPlatform(this.new_platform).subscribe(
      (data) => {
        this.visible = false;
        this.loadRegisteredPlatforms();
        this.resetPlatform();
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Platform Created', life: 3000 });
      },
      (err) => {
        console.log("Compose Message | Error creating platform ", err);
        this.visible = false;
        this.resetPlatform();
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Platform Creation Failed', sticky: true });
      }
    )
  }

  onSave() {
    let platFormCount = 0;
    for (let platform of this.platforms) {
      platform.owner_id = this.user.id;
      this.platforService.updatePlatform(platform).subscribe(
        (data) => {
          console.log("Platform Token ", platform.token);
          console.log(platform);
          platFormCount += 1;
          if (platFormCount === this.platforms.length) {
            this.loadRegisteredPlatforms();
            this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Platforms Updated', life: 3000 });
          }
        },
        (err) => {
          platFormCount += 1;
          console.log("Profile | Error updating platforms ", err);
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Platforms Update Failed', sticky: true });
          return;
        }
      );
    }
  }
}

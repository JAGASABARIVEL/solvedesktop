import { Component, ElementRef, isStandalone, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MenuItem } from 'primeng/api';

import { LayoutService } from "./service/app.layout.service";
import { SplitButtonModule } from 'primeng/splitbutton';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-topbar',
    templateUrl: './app.topbar.component.html',
    standalone: true,
    imports: [
        CommonModule,
        SplitButtonModule
    ]

})
export class AppTopBarComponent {

    items!: MenuItem[];

    @ViewChild('menubutton') menuButton!: ElementRef;

    @ViewChild('topbarmenubutton') topbarMenuButton!: ElementRef;

    @ViewChild('topbarmenu') menu!: ElementRef;

    constructor(private router: Router, public layoutService: LayoutService) {
        this.items = [
            {
                icon: 'pi pi-user',
                label: 'Profile',
                command: () => {
                    this.profileViewButton();
                }
            },
            {
                icon: 'pi pi-sign-out',
                label: 'Logout',
                command: () => {
                    this.logoutButton();
                }
            }
        ];
    }

    profileViewButton() {
        this.router.navigate(['me']);
    }

    logoutButton() {
        localStorage.clear();
        this.router.navigate(['login']);
    }

    
}

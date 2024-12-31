import { OnInit } from '@angular/core';
import { Component } from '@angular/core';
import { LayoutService } from './service/app.layout.service';

@Component({
    selector: 'app-menu',
    templateUrl: './app.menu.component.html'
})
export class AppMenuComponent implements OnInit {

    model: any[] = [];

    constructor(public layoutService: LayoutService) { }

    ngOnInit() {
        this.model = [
            {
                label: 'Home',
                icon: 'pi pi-fw pi-briefcase',
                items: [
                    {
                        label: 'Products',
                        icon: 'pi pi-home',
                        items: [
                            {
                                label: 'Schedule',
                                icon: 'pi pi-fw pi-calendar',
                                routerLink: ['/schedule']
                            },
                            {
                                label: 'Manage Contacts',
                                icon: 'pi pi-address-book',
                                routerLink: ['/contacts']
                            },
                            {
                                label: 'Chat',
                                icon: 'pi pi-comment',
                                routerLink: ['/chat']
                            },
                        ]
                    },
                ]
            }
        ];
    }
}

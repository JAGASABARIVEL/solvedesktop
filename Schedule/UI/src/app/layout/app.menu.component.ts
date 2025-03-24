import { OnInit } from '@angular/core';
import { Component } from '@angular/core';
import { LayoutService } from './service/app.layout.service';
import { AppMenuitemComponent } from './app.menuitem.component';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-menu',
    templateUrl: './app.menu.component.html',
    standalone: true,
    imports: [
        CommonModule,
        AppMenuitemComponent
    ]
})
export class AppMenuComponent implements OnInit {

    model: any[] = [];

    constructor(public layoutService: LayoutService) { }

    ngOnInit() {
        this.model = [
            {
                label: 'Home',
                icon: 'pi pi-home',
                items: [
                    {
                        label: 'Dashboard',
                        icon: 'pi pi-fw pi-home',
                        routerLink: ['/']
                    }
                ]
            },
            {
                label: 'Apps',
                icon: 'pi pi-home',
                items: [
                    {
                        label: 'Contacts',
                        icon: 'pi pi-address-book',
                        routerLink: ['/contacts']
                    },
                    {
                        label: 'Campaign',
                        icon: 'pi pi-megaphone',
                        routerLink: ['/schedule']
                    },
                    {
                        label: 'Customer Service',
                        icon: 'pi pi-users',
                        items: [
                            {
                                label: 'Chat',
                                icon: 'pi pi-comment',
                                routerLink: ['/chat']
                            }
                        ],
                    },
                    //{
                    //    label: 'Task',
                    //    icon: 'pi pi-fw pi-briefcase',
                    //    routerLink: ['/projects/1/tasks/1']
                    //},
                ]
            }
        ];
    }
}

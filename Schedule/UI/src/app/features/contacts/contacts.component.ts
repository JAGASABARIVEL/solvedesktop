
import { Component, OnInit } from '@angular/core';
import { TabViewModule } from 'primeng/tabview';
import { BadgeModule } from 'primeng/badge';

import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ContactComponent } from './contact/contact.component';

@Component({
  selector: 'app-contacts',
  standalone: true,
  imports: [
    CommonModule,
    TabViewModule,
    BadgeModule,

    ContactComponent
  ],
  providers: [],
  templateUrl: './contacts.component.html',
  styleUrl: './contacts.component.scss'
})
export class ContactsComponent {

  total_contacts: number = 0;
  total_groups: number = 0;

  constructor(private router: Router) {}

  ngOnInit(): void {
    const profile = JSON.parse(localStorage.getItem('me'));

    if (!profile) {
      this.router.navigate(['login']);
    }
  }

  onTotalContactsHandler(count: number) {
    this.total_contacts = count;
  }

  onTotalGroupsHandler(count: number) {
    this.total_groups = count;
  }


  
}


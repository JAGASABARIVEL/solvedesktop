import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ConversationDashboardComponent } from './conversation-dashboard/conversation-dashboard.component';
import { TabViewModule } from 'primeng/tabview';
import { KeyloggerDashboardComponent } from './keylogger-dashboard/keylogger-dashboard.component';


@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ConversationDashboardComponent,
    KeyloggerDashboardComponent,

    TabViewModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {

}

import { Component, OnInit } from '@angular/core';
import { TabViewModule } from 'primeng/tabview';
import { BadgeModule } from 'primeng/badge';
import { ComposeMessageComponent } from './compose-message/compose-message.component';
import { CrudSchedulesComponent } from './crud-schedules/crud-schedules.component';
import { UsageChargesComponent } from './usage-charges/usage-charges.component';
import { MessageHistoryComponent } from './message-history/message-history.component';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-schedule',
  standalone: true,
  imports: [
    CommonModule,
    TabViewModule,
    BadgeModule,

    ComposeMessageComponent,
    CrudSchedulesComponent,
    MessageHistoryComponent
  ],
  templateUrl: './schedule.component.html',
  styleUrl: './schedule.component.scss'
})
export class ScheduleComponent implements OnInit {

  failedMessageCounts: number = 0;
  total_schedules: number = 0;

  constructor(private router: Router) {}
  ngOnInit(): void {
    const profile = JSON.parse(localStorage.getItem('me'));

    if (!profile) {
      this.router.navigate(['login']);
    }
  }

  onTotalSchedulesHandler(count: number) {
    this.total_schedules = count;
  }

  onFailedMessageHandler(count: number) {
    this.failedMessageCounts = count;
  }

}

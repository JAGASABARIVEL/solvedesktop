import { Component, OnInit } from '@angular/core';
import { TabViewModule } from 'primeng/tabview';
import { BadgeModule } from 'primeng/badge';
import { ComposeMessageComponent } from './compose-message/compose-message.component';
import { CrudSchedulesComponent } from './crud-schedules/crud-schedules.component';
import { UsageChargesComponent } from './usage-charges/usage-charges.component';
import { MessageHistoryComponent } from './message-history/message-history.component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-schedule',
  standalone: true,
  imports: [
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

  constructor(private router: Router) {}
  ngOnInit(): void {
    const profile = JSON.parse(localStorage.getItem('me'));

    if (!profile) {
      this.router.navigate(['login']);
    }
  }

}

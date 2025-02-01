import { Component, EventEmitter, OnInit, Output, output } from '@angular/core';
import { TableModule, Table } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { HttpClientModule } from '@angular/common/http';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ScheduleService } from '../../../shared/services/Schedule/schedule.service';
import { MessageHistoryModel } from './message-history.model';
import { ToolbarModule } from 'primeng/toolbar';
import { ButtonModule } from 'primeng/button';
@Component({
  selector: 'app-message-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,

    ToolbarModule,
    ButtonModule,
    TableModule,
    TagModule,
    IconFieldModule,
    InputTextModule,
    InputIconModule,
    MultiSelectModule,
    DropdownModule,
    HttpClientModule,
    
  ],
  templateUrl: './message-history.component.html',
  styleUrl: './message-history.component.scss'
})
export class MessageHistoryComponent implements OnInit {
    @Output() onFailedMessage: EventEmitter<number> = new EventEmitter();
    messages!: MessageHistoryModel[];
    loading: boolean = false;
    failed_message_count = 0;
    profile !: any;

    constructor(private router: Router, private scheduleService: ScheduleService) {}
  ngOnInit(): void {

    this.profile = JSON.parse(localStorage.getItem('me'));
        if (!this.profile) {
          this.router.navigate(['login']);
        }
        this.loadHistory();
        
  }

  loadHistory() {
    this.loading = true;
        this.scheduleService.getHistory(this.profile.organization).subscribe(
          (data: MessageHistoryModel[]) => {
            this.messages = data;
            this.messages.forEach((message) => (message.send_date = new Date(<Date>message.send_date)));
            this.getFailedMessageCount();
            this.loading = false;
          },
          (err) => {
            console.log("Compose Message | Error getting history ", err);
            this.loading = false;
          }
        );

  }

  getFailedMessageCount() {
    this.failed_message_count = 0;
    this.messages.forEach((message) => {
      if (message.status == 'Error') {
        this.failed_message_count++;
      }
    });
    if (this.failed_message_count > 0) {
      this.onFailedMessage.emit(this.failed_message_count);
    }
  }
}

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { Table, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ToolbarModule } from 'primeng/toolbar';
import { Subscription } from 'rxjs';
import { ConversationModel } from '../../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../../shared/services/Conversation/conversation.service';
import { ScheduleEventService } from '../../../shared/services/Events/schedule-events.service';
import { OrganizationService } from '../../../shared/services/Organization/organization.service';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';

@Component({
  selector: 'app-list-conversations',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DropdownModule,
    InputTextModule,
    TagModule,
    AvatarModule,
    ToastModule,
    ToolbarModule,
    ButtonModule,
    TableModule,
    ConfirmDialogModule,
    InputGroupModule,
    InputGroupAddonModule
  ],
  providers: [
    MessageService, ConfirmationService
  ],
  templateUrl: './list-conversations.component.html',
  styleUrl: './list-conversations.component.scss'
})
export class ListConversationsComponent implements OnInit, OnDestroy {
  @Output() totalConversations: EventEmitter<number> = new EventEmitter();
  profile !: any;
  susbscription!: Subscription;

  users!: any[];
  conversation !: ConversationModel;
  conversations!: ConversationModel[];
  selectedConversations!: ConversationModel[];
  loading: boolean = false;

  constructor(
    private router: Router,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private conversationService: ConversationService,
    private organizationService: OrganizationService,
    private assignmentEventService: ScheduleEventService
  ) { }
  ngOnDestroy(): void {
    this.susbscription?.unsubscribe();
  }
  ngOnInit(): void {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.loadConversations();
    this.loadUsers();
    // From websocket. TODO: May be we need to move the websocket appropriate location
    this.subscribeForNewConversations();
  }

  loadUsers() {
    this.organizationService.fetch_organization_by_id(this.profile.organization).subscribe((data) => {
      console.log("data ", data);
      this.users = data.employees;
    },
    (err) => {
      console.log("List conversation | Error getting users ", err);
    }
    );
  }

  subscribeForNewConversations() {
    this.susbscription = this.assignmentEventService.newConversationEvent$.subscribe((event)=> {
      this.loadConversations();
    });
  }

  loadConversations(skip_notification=true) {
    this.loading = true;
    this.conversationService.getAllConversations(
      {"organization_id": this.profile.organization, "conversation_status": "new"}
    ).subscribe((data) => {
      this.totalConversations.emit(data.length);
      this.conversations = data;
      console.log("List conversations | new conversations ", data);
      this.loading = false;
      if (!skip_notification){
        this.assignmentEventService.emitAssignmentChange("Assignment Change");
      }
    },
    (err) => {
      console.log("List conversation | Error getting conversations ", err);
      this.loading = false;
    }
    )
  }

  onSearchInput(event: Event, dt: Table): void {
    const inputElement = event.target as HTMLInputElement;
    const searchValue = inputElement.value;
    dt.filterGlobal(searchValue, 'contains');
  }

  getSeverity(status: string) {
    switch (status) {
        case 'new':
            return 'danger';
        case 'active':
            return 'warn';
        case 'closed':
            return 'success';
    }
    return 'danger';
  }

  toggleDropdown(row: any): void {
    row.isDropdownVisible = !row.isDropdownVisible;
  }

  assignTask(row: any): void {
    console.log("assigned ",row.assigned);
    if (row.assigned) {
      this.conversationService.assign(
        row.conversation_id,
        row.assigned
      ).subscribe((data) => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: `Task "${row.conversation_id}" assigned to: ${row.assigned.name}` });
        this.loadConversations(false);
      },
      (err) => {
        console.log("List conversation | Error assigning task ", err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while assigning task', sticky: true });
      }
      )
      row.isDropdownVisible = false; // Close dropdown after assignment
    }
  }

  cancelAssignment(row: any): void {
    row.isDropdownVisible = false; // Close dropdown without assigning
    row.assigned = null; // Clear selection
  }


}

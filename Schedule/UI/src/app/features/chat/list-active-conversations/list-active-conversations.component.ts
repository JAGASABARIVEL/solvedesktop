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
import { InputGroupAddon } from 'primeng/inputgroupaddon';
import { DialogModule } from 'primeng/dialog';


@Component({
  selector: 'app-list-active-conversations',
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
    InputGroupAddon,
    DialogModule
  ],
  templateUrl: './list-active-conversations.component.html',
  styleUrl: './list-active-conversations.component.scss'
})
export class ListActiveConversationsComponent implements OnInit, OnDestroy {
  @Output() totalActiveConversations: EventEmitter<number> = new EventEmitter();
  profile !: any;
  assignmentChangeSubscription: Subscription;
  assignmentClosedSubscription: Subscription;
  existingAssignee: any;

  users!: any[];
  conversation !: any;
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
    this.assignmentChangeSubscription?.unsubscribe();
    this.assignmentClosedSubscription?.unsubscribe();
  }
  ngOnInit(): void {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.susbscribeAssignemntChangeEvent();
    this.subscribeCloseConversationEvent();
    this.loadConversations();
    this.loadUsers();
  }

  susbscribeAssignemntChangeEvent() {
    this.assignmentChangeSubscription = this.assignmentEventService.assignmentEvent$.subscribe((convs) => {
      if (convs !== 'skip') {
        this.loadConversations();
      }
    });
  }

  subscribeCloseConversationEvent() {
    this.assignmentClosedSubscription = this.assignmentEventService.closeConversationEvent$.subscribe((message) => {
      if (message !== 'skip') {
        this.loadConversations();
      }
    })
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

  loadConversations() {
    this.loading = true;
    this.conversationService.getAllConversations(
      {
        "organization_id": this.profile.organization,
        "conversation_status": "active"
      }
    ).subscribe((data) => {
      this.totalActiveConversations.emit(data.length);
      this.conversations = data;
      this.loading = false;
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
    this.existingAssignee = row.assigned;
  }

  assignTask(row: any): void {
    console.log("assigned ",row.assigned);
    if (row.assigned) {
      this.conversationService.assign(
        row.conversation_id,
        row.assigned
      ).subscribe((data) => {
        this.assignmentEventService.emitAssignmentChange('skip');
        this.loadConversations();
        this.messageService.add({ severity: 'success', summary: 'Success', detail: `Task "${row.conversation_id}" assigned to: ${row.assigned.name}` });
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
    row.assigned = this.existingAssignee; // Clear selection
  }

  closeConversationVisible = false;
  closedReason;
  selectedConversation;
  closePreTask(conversation) {
    this.closeConversationVisible = true;
    this.selectedConversation = conversation
    console.log("this.selectedConversation ", this.selectedConversation);
  }
  closeTask() {
    this.conversationService.close(
      this.selectedConversation.conversation_id,
      {
        "closed_by": this.profile.id,
        "closed_reason": this.closedReason
      }
    ).subscribe((data)=>{
      this.closeConversationVisible = false;
      console.log("Conversation closed ", data);
      //this.sortUserConversationsByStatus();
      //this.updateNewConversationList();
      this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Conversation closed successfully' });
      //this.deleteSpecificConversation(this.activeUser);
      //this.refreshFilterList();
      this.loadConversations();
      this.assignmentEventService.emitCloseConversation("skip");
    });
  }
}

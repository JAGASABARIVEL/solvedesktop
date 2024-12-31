import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { Router } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { InputTextModule } from 'primeng/inputtext';
import { Table, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ToolbarModule } from 'primeng/toolbar';
import { ConversationModel } from '../../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../../shared/services/Conversation/conversation.service';

@Component({
  selector: 'app-list-conversations',
  standalone: true,
  imports: [
    InputTextModule,
    TagModule,
    AvatarModule,
    ToastModule,
    ToolbarModule,
    ButtonModule,
    TableModule,
    ConfirmDialogModule
  ],
  templateUrl: './list-conversations.component.html',
  styleUrl: './list-conversations.component.scss'
})
export class ListConversationsComponent implements OnInit {
  @Output() totalConversations: EventEmitter<number> = new EventEmitter();
  profile !: any;

  conversation !: ConversationModel;
  conversations!: ConversationModel[];
  selectedConversations!: ConversationModel[];
  loading: boolean = false;

  constructor(
    private router: Router,
    private conversationService: ConversationService
  ) { }
  ngOnInit(): void {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.loadConversations();
  }

  loadConversations() {
    this.loading = true;
    this.conversationService.getAllConversations(
      {"organization_id": this.profile.organization}
    ).subscribe((data) => {
      this.totalConversations.emit(data.length);
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
            return 'warning';
        case 'closed':
            return 'success';
    }
    return 'danger';
  }

}

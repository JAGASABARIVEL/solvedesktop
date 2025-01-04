import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { BadgeModule } from 'primeng/badge';
import { TabViewModule } from 'primeng/tabview';
import { ChatWindowComponent } from './chat-window/chat-window.component';
import { ListActiveConversationsComponent } from './list-active-conversations/list-active-conversations.component';
import { ListConversationsComponent } from './list-conversations/list-conversations.component';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    TabViewModule,
    BadgeModule,

    ListConversationsComponent,
    ListActiveConversationsComponent,
    ChatWindowComponent
  ],
  providers: [
    MessageService,
    ConfirmationService
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {
  total_conversations: number = 0;
  total_new_conversation_me: number = 0;
  total_active_conversations: number = 0;

  constructor(private router: Router) {}

  ngOnInit(): void {
    const profile = JSON.parse(localStorage.getItem('me'));

    if (!profile) {
      this.router.navigate(['login']);
    }
  }

  onTotalConversationsHandler(count: number) {
    this.total_conversations = count;
  }

  onTotalNewConversationsMeHandler(count: number) {
    this.total_new_conversation_me = count;
  }

  onTotalActiveConversationsHandler(count: number) {
    this.total_active_conversations = count;
  }
}

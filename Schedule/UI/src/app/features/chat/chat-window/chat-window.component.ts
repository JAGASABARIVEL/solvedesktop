import { CommonModule } from '@angular/common';
import { AfterViewChecked, ChangeDetectorRef, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ConversationModel, UserMessages } from '../../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../../shared/services/Conversation/conversation.service';
import { STATUSES } from './models';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,

    AvatarModule,
    CardModule,
    InputTextModule,
    ButtonModule
  ],
  templateUrl: './chat-window.component.html',
  styleUrl: './chat-window.component.scss'
})
export class ChatWindowComponent implements OnInit, AfterViewChecked, OnDestroy  {
  statuses = STATUSES;
  messageReceivedFrom = {
    img: 'https://cdn.livechat-files.com/api/file/lc/img/12385611/371bd45053f1a25d780d4908bde6b6ef',
    name: 'Media bot'
  }

  profile !: any;

  users: any[] = []; // Replace with your fetched user list
  activeUser!: any;
  expanded: boolean = false;
  expandStatuses: boolean = false;
  webSocket: WebSocket | null = null; // WebSocket instance

  @ViewChild('scrollMe') private myScrollContainer: ElementRef;

    constructor(
      private cdr: ChangeDetectorRef,
      private router: Router,
      private conversationService: ConversationService
    ) { }

    ngOnInit() { 

      this.profile = JSON.parse(localStorage.getItem('me'));
      if (!this.profile) {
        this.router.navigate(['login']);
      }
      this.loadConversations();
      //this.scrollToBottom();
    }
    ngAfterViewChecked() {        
      this.scrollToBottom();   
    }

    loadConversations() {
        this.conversationService.getAllConversations(
          {"organization_id": this.profile.organization}
        ).subscribe(
          (data) => {
            this.users = data.map((conversation) => ({
              id: conversation.contact.id,
              name: conversation.contact.name,
              phone: conversation.contact.phone,
              conversationId: conversation.conversation_id,
              messages: conversation.messages,
              img: 'http://emilcarlsson.se/assets/louislitt.png', // You can replace this with actual avatar if available
              status: conversation.active, // Add default status for demo purposes
            }));
            this.setUserActive(this.users[0]);
          },
          (err) => {
            console.log("Chat window | Error getting conversations ", err);
          }
        );
    }

    setUserActive(user: any): void {
      // Close any existing WebSocket connection
      if (this.webSocket) {
        this.webSocket.close();
        this.webSocket = null;
      }
  
      this.activeUser = user;
  
      // Fetch messages for the active user
      this.fetchConversation(user.conversationId);
  
      // Establish a WebSocket connection
      //this.connectWebSocket(user.conversationId);

      // Trigger change detection manually
      this.cdr.detectChanges();
    }

    fetchConversation(conversationId: number): void {
      this.conversationService.getConversationFromId(conversationId).subscribe(
        (conversation: ConversationModel) => {
          this.activeUser.messages = conversation.messages;
          console.log("this.activeUser.messages ", this.activeUser.messages);
        },
        (error) => {
          console.error('Error fetching conversation:', error);
        }
      );
    }

    connectWebSocket(conversationId: number): void {
      const wsUrl = `ws://localhost:5000/chat/conversations/${conversationId}`;
      this.webSocket = new WebSocket(wsUrl);
  
      this.webSocket.onopen = () => {
        console.log(`WebSocket connected for conversation ${conversationId}`);
      };
  
      this.webSocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.activeUser.messages.push(message);
        this.scrollToBottom();
      };
  
      this.webSocket.onclose = () => {
        console.log(`WebSocket closed for conversation ${conversationId}`);
      };
  
      this.webSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    }

    addNewMessage(input: HTMLInputElement): void {
      const messageText = input.value.trim();
      if (!messageText || !this.webSocket || this.webSocket.readyState !== WebSocket.OPEN) {
        return;
      }
  
      const message = {
        type: 'org',
        message_body: messageText,
        sent_time: new Date().toISOString(),
      };
  
      this.webSocket.send(JSON.stringify(message));
      this.activeUser.messages.push(message);
      input.value = '';
      this.scrollToBottom();
    }

    scrollToBottom(): void {
      setTimeout(() => {
        this.myScrollContainer.nativeElement.scrollTop = this.myScrollContainer.nativeElement.scrollHeight;
      }, 0);
    }

    ngOnDestroy(): void {
      if (this.webSocket) {
        this.webSocket.close();
        this.webSocket = null;
      }
    }

    /**
    scrollToBottom(): void {
        try {
            this.myScrollContainer.nativeElement.scrollTop = this.myScrollContainer.nativeElement.scrollHeight;
        } catch(err) { }                 
    }
    */

    /**
    connectToWS() {
      if (this.activeUser.ws && this.activeUser.ws.readyState !== 1) {
        this.activeUser.ws = null;
        this.activeUser.status = STATUSES.OFFLINE;
      }
      if (this.activeUser.ws) {
        return;
      }
      const ws = new WebSocket('wss://compute.hotelway.ai:4443/?token=TESTTOKEN');
      this.activeUser.ws = ws;
      ws.onopen = (event) => this.onWSEvent(event, STATUSES.ONLINE);
      ws.onclose = (event) => this.onWSEvent(event, STATUSES.OFFLINE);
      ws.onerror = (event) => this.onWSEvent(event, STATUSES.OFFLINE);
      ws.onmessage = (result: any) => {
        const data = JSON.parse(result?.data || {});
        const userFound = this.users.find(u => u.id === data.id);
        if (userFound) {
          userFound.messages.push(
             new Message('customer', data.message)
          )
        }
      };
    }

    onWSEvent(event, status: STATUSES) {
      this.users.forEach(u => u.ws === event.target ? u.status = status : null)
    }
}
function heartbeat() {
  clearTimeout(this.pingTimeout);

  // Use `WebSocket#terminate()`, which immediately destroys the connection,
  // instead of `WebSocket#close()`, which waits for the close timer.
  // Delay should be equal to the interval at which your server
  // sends out pings plus a conservative assumption of the latency.
  this.pingTimeout = setTimeout(() => {
    this.terminate();
  }, 30000 + 1000);
  */
}

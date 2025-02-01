import { CommonModule } from '@angular/common';
import { AfterViewChecked, ChangeDetectorRef, Component, ElementRef, EventEmitter, OnDestroy, OnInit, Output, ViewChild } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';
import { Subscription } from 'rxjs';
import { ConversationResponseModel } from '../../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../../shared/services/Conversation/conversation.service';
import { SocketService } from '../../../shared/services/Conversation/socketio.service';
import { ScheduleEventService } from '../../../shared/services/Events/schedule-events.service';
import { OrganizationService } from '../../../shared/services/Organization/organization.service';
import { STATUSES } from './models';
import { ContactService } from '../../../shared/services/Contact/contact.service';
import { DropdownModule } from 'primeng/dropdown';
import { ConfirmPopupModule } from 'primeng/confirmpopup'; 
import { PlatformService } from '../../../shared/services/Platform/platform.service';
import { DialogModule } from 'primeng/dialog';
import { TooltipModule } from 'primeng/tooltip';
import { query } from '@angular/animations';
import { SelectModule } from 'primeng/select';


@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,

    TooltipModule,
    AvatarModule,
    CardModule,
    InputTextModule,
    ButtonModule,
    CardModule,
    BadgeModule,
    ToastModule,
    SelectModule,
    DialogModule,
    ConfirmPopupModule
  ],
  providers: [
    MessageService,
    ConfirmationService
  ],
  templateUrl: './chat-window.component.html',
  styleUrl: './chat-window.component.scss'
})
export class ChatWindowComponent implements OnInit, AfterViewChecked, OnDestroy  {
  @Output() newUniqueConversationMessageCount: EventEmitter<any> = new EventEmitter();
  total_new_conversation_count = [];
  assignmentChangeSubscription: Subscription;
  statuses = STATUSES;
  messageReceivedFrom = {
    img: 'https://cdn.livechat-files.com/api/file/lc/img/12385611/371bd45053f1a25d780d4908bde6b6ef',
    name: 'Media bot'
  }

  loadContactId = undefined;

  profile !: any;
  robo_profile !: any;

  employees: any[];
  users: any[] = []; // Replace with your fetched user list
  activeUser!: any;
  filteredUsers: any[] = [];
  searchQuery: string = '';
  expanded: boolean = false;
  expandStatuses: boolean = false;
  closedReason: string = 'NA';
  conversationResponse!: ConversationResponseModel;
  private messageSubscription: Subscription | undefined;

  @ViewChild('scrollMe') private myScrollContainer: ElementRef;

    constructor(
      private cdr: ChangeDetectorRef,
      private router: Router,
      private messageService: MessageService,
      private confirmationService: ConfirmationService,
      private conversationService: ConversationService,
      private socketService: SocketService,
      private organizationService: OrganizationService,
      private assignmentEventService: ScheduleEventService,
      private contactService: ContactService,
      private platforService: PlatformService
    ) { }

    ngOnInit() {
      this.profile = JSON.parse(localStorage.getItem('me'));
      
      if (!this.profile) {
        this.router.navigate(['login']);
      }
      this.robo_profile = this.organizationService.fetch_robo_detail(this.profile.organization).subscribe(
        (robo_detail) => {
          this.robo_profile = robo_detail;
        }
      );
      this.loadRegisteredPlatforms();
      this.susbscribeAssignemntChangeEvent();
      this.loadContacts();
      this.loadUsers();
      this.connectWebSocket();
      //this.scrollToBottom();
    }
    ngAfterViewChecked() {        
      this.scrollToBottom();   
    }

    susbscribeAssignemntChangeEvent() {
      this.assignmentChangeSubscription = this.assignmentEventService.assignmentEvent$.subscribe(() => {
        this.loadConversations();
      });
    }

    private usedColors: Set<string> = new Set();

    currentColor: string = '#FFFFFF';

    generateColor(): void {
      this.currentColor = this.getRandomColor();
    }
  
    getRandomColor(): string {
      return '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
    }

    getUniqueRandomColor(): string {
      let color;
      do {
        color = this.getRandomColor();
      } while (this.usedColors.has(color));
      this.usedColors.add(color);
      return color;
    }

    loadUsers() {
      this.organizationService.fetch_organization_by_id(this.profile.organization).subscribe((data) => {
        console.log("data ", data);
        this.employees = data.employees;

        this.employees.forEach(
          (emp) => {
            emp.color = this.getUniqueRandomColor();
          }
        );
        console.log("Employees color ", this.employees);
        this.loadConversations();
      },
      (err) => {
        console.log("List conversation | Error getting users ", err);
      }
      );
    }

    getEmployeeNameFromId(id) {
      const employee = this.employees.find(employee => employee.id === id);
      return employee || {"name": "unknown", "color": "red"};
    }

    filterContacts() {
      const query = this.searchQuery.toLowerCase();

      this.filteredUsers = this.users.filter(user =>
        user.name.toLowerCase().includes(query) || 
        user.phone.toLowerCase().includes(query)
      );
      // When the user removes the search text while there is no active conversation
      if (query.length === 0 && !this.activeUser) {
        this.filteredUsers = this.filteredUsers
      }
      else if (query.length === 0 && this.activeUser && this.filteredUsers.length === 0) {
        this.filteredUsers = [this.activeUser];
      }
      else if (query.length > 0 && this.filteredUsers.length === 0) {
        this.filteredUsers = this.all_contacts.filter(user =>
          user.name.toLowerCase().includes(query) || 
          user.phone.toLowerCase().includes(query)
        );
      }
    }

    getUnreadCount(msgs) {
      let count = 0;
      for(let msg of msgs) {
        if (msg.status === 'unread') {
          count++;
        }
      }
      return count;
    }

    connectWebSocket(): void {
      this.messageSubscription = this.socketService.getMessages().subscribe((message) => {
        console.log('Received message:', message);
        console.log("this.users ", this.users);
        if (message.msg_from_type === "CUSTOMER") {
          const user = this.users.find((user) => user.conversationId === message.conversation_id);
          if (user) {
            user.messages.push(message);
          } else {
            console.warn(`User with conversationId ${message.conversation_id} not found.`);
            this.assignmentEventService.emitNewConversation("New conversation");
            //this.conversationService.getConversationFromId(
            //  message.conversation_id,
            //  {"assignee": this.profile.id}
            //).subscribe((conv) => {
            //  this.users.push(
            //  {
            //    id: conv.contact.id,
            //    name: conv.contact.name,
            //    phone: conv.contact.phone,
            //    conversationId: conv.conversation_id,
            //    messages: conv.messages,
            //    img: 'http://emilcarlsson.se/assets/louislitt.png', // You can replace this with actual avatar if available
            //    status: conv.status,
            //});
            //  this.filteredUsers = [...this.users]; // Initially display all users
            //  console.log("Reloaded the conversation for active user");
            //});
          }
          this.updateNewConversationList();
          console.log("this.users ", this.users);
          this.scrollToBottom();
          //this.messages.push(message); // Add the received message to the messages array
        }
        else if (message.msg_from_type === "ORG") {
          // Reload specific conversation since we have a notification that the message status has been updated
          // for one of the message in this conversation.
          const user = this.users.find((user) => user.conversationId === message.conversation_id);
          if (user) {
            this.conversationService.getConversationFromId(
              user.conversationId,
              {"assignee": this.profile.id}
            ).subscribe((conv) => {
              user.messages = conv.messages;
            });
          }
        }
      });
    }

    updateNewConversationList() {
      this.total_new_conversation_count = [];
      this.users.forEach((user) => {
        for (let i = 0; i < user.messages.length; i++) {
          if (user.messages[i]?.status === 'unread') {
            this.total_new_conversation_count.push(user);
            break;
          }
        }
      });
      this.newUniqueConversationMessageCount.emit(this.total_new_conversation_count.length);
    }

    getFlattenedMessages(messages: any[]): any[] {
      const flattened: any[] = [];
      messages.forEach((msg) => {
        if (Array.isArray(msg)) {
          flattened.push(...msg); // Spread nested messages
        } else {
          flattened.push(msg); // Add single message
        }
      });
      return flattened;
    }
    
    loadHistoricalConversation() {
      this.loadContactId = this.activeUser.id;
      console.log("this.activeUser.id ", this.activeUser.id);
    
      this.conversationService.getAllConversations({
        "organization_id": this.profile.organization,
        "contact_id": this.activeUser.id,
        "conversation_status": "new,closed,active"
      }).subscribe(
        (convs) => {
          console.log("History data ", convs);
    
          let user = this.users.find((us) => us.id === this.loadContactId);
          if (!user) {
            user = this.all_contacts.find((us) => us.id === this.loadContactId);
          }
    
          let conv_messages: any[] = [];
    
          convs.forEach((conv) => {
            // Add start_tag
            conv_messages.push({
              'type': 'start_tag',
              'by': conv.open_by,
              'reason': conv.open_by === 'customer' ? 'Customer Query' : 'Organization Query',
              'timestamp': new Date(conv.created_at).getTime()
            });
    
            // Extract and normalize messages
            conv.messages.forEach((msg: any) => {
              conv_messages.push({
                ...msg,
                'timestamp': msg.sent_time ? new Date(msg.sent_time).getTime() : new Date(msg.received_time).getTime()
              });
            });
    
            // Add end_tag if conversation is closed
            if (conv.status === 'closed') {
              conv_messages.push({
                'type': 'end_tag',
                'by': this.getEmployeeNameFromId(conv.closed_by)?.name || "Unknown",
                'reason': conv.closed_reason,
                'timestamp': new Date(conv.created_at).getTime() + 1 // Ensure it appears at the end
              });
            }
          });
    
          // Sort messages chronologically
          conv_messages.sort((a, b) => a.timestamp - b.timestamp);
    
          user.messages = conv_messages;
          console.log("this.users ", this.users);
        },
        (err) => {
          console.log("Chat window | Error getting historical conversations ", err);
        }
      );
    }
    

    getCardBackgroundColor(user: any): string {
      if (user.id === this.activeUser.id) {
        console.log("Returning teal");
        return 'teal';
      }
      if (user.status === 'closed') {
        console.log("Returning red");
        return 'red';
      }
      console.log("Returning white");
      return 'white';
    }

    refreshFilterList() {
      this.filteredUsers = [...this.users];
    }

    sortUserConversationsByStatus() {
      this.refreshFilterList();
      this.filteredUsers.sort((a, b)=> {
        if (a.status === 'closed' && b.status !== 'closed') {
          return 1;
        }
        if (a.status !== 'closed' && b.status === 'closed') {
          return -1;
        }
        return 0;
      });
    }

    loadConversations() {
        this.conversationService.getAllConversations(
          {
            "organization_id": this.profile.organization,
            "assignee": this.profile.id,
            "conversation_status": "new,active"         
          }
        ).subscribe(
          (data) => {
            console.log("raw data ", data);
            this.users = data.map((conversation) => ({
              id: conversation.contact.id,
              name: conversation.contact.name,
              phone: conversation.contact.phone,
              conversationId: conversation.conversation_id,
              messages: conversation.messages,
              img: 'http://emilcarlsson.se/assets/louislitt.png', // You can replace this with actual avatar if available
              status: conversation.status, // Add default status for demo purposes
              assignee: this.profile.id
            }));
            console.log("this.users ", this.users);
            this.sortUserConversationsByStatus()
            this.setUserActive(this.users[0]);
            this.updateNewConversationList();
          },
          (err) => {
            console.log("Chat window | Error getting conversations ", err);
          }
        );
    }

    all_contacts = []
    loading = false;

    loadContacts() {
      this.loading = true;
      let new_users = []
      this.contactService.getContacts({"organization_id": this.profile.organization}).subscribe(
        (data) => {
          this.loading = false;
          this.all_contacts = data.map((contact) => ({
            id: contact.id,
            name: contact.name,
            phone: contact.phone,
            messages: [],
            img: 'http://emilcarlsson.se/assets/louislitt.png', // You can replace this with actual avatar if available
            status: 'org_new', // Add default status for demo purposes
            assignee: -1
          }));
          this.conversationService.getAllConversations({
            "organization_id": this.profile.organization,
            "conversation_status": "new,active"
          }).subscribe((conts_data: any[]) => {
            conts_data.forEach((cont_data: any)=>{
              console.log("cont_data.contact ", cont_data.contact.id)
              let foundIndex = this.all_contacts.findIndex((all_cont) => all_cont.id === cont_data.contact.id);
              console.log("foundIndex ", foundIndex)
              console.log(this.all_contacts);
              if (foundIndex >= 0) {
                this.all_contacts[foundIndex].status = cont_data.status;
                this.all_contacts[foundIndex].conversation_id = cont_data.conversation_id;
                this.all_contacts[foundIndex].assignee = cont_data.assigned?.id;
              }
              
            });
          })
          console.log("all_contacts ", this.all_contacts);
          this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Contacts Loaded', life: 3000 });
        },
        (err) => {
          this.loading = false;
          console.log("Contacts | Error getting contacts ", err);
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Contacts Not Loaded', sticky: true });
        }
      );
    }
    

    setUserActive(user: any): void {
      this.activeUser = user;
      this.cdr.detectChanges();
    }


    moveUserConversationToTop(userObject) {
      const [deletedUserObject] = this.deleteSpecificConversation(userObject);
      this.users.unshift(deletedUserObject);
      this.refreshFilterList();
      console.log("After shifting ", this.users);
    }

    addNewMessage(input: HTMLInputElement): void {
      const messageText = input.value.trim();
      if (!messageText) {
        return;
      }

      this.conversationResponse = {
        conversation_id: this.activeUser.conversationId,
        message_body: messageText,
        user_id: this.profile.id
      }

      let msg_text = input.value;
      this.activeUser.status = 'active' // In case the conversation is already closed
      this.activeUser.messages.push({message_body: msg_text, sender: this.profile.id, sent_time : Date(),  status : "unknown", type: "org"});
      input.value = '';
      this.searchQuery = '';



      this.conversationService.respond(
        this.conversationResponse
      ).subscribe((data) => {
        this.conversationService.getConversationFromId(
          this.activeUser.conversationId,
          {"assignee": this.profile.id}
        ).subscribe((conv) => {
          this.activeUser.status = 'active' // In case the conversation is already closed
          this.activeUser.messages = conv.messages;
          this.updateNewConversationList();
          this.moveUserConversationToTop(this.activeUser);
          // Clear the serach query for usability since we don';t know when to clear
          // the query since user can simply search as well but here its guranteed he/she
          // could have finalized the search and sent the message.
          // Note: This is neat since we are also resetting the filterUsers
          //       through moveUserConversationToTop
          this.searchQuery = '';

          input.value = '';
          this.scrollToBottom();
          console.log("Reloaded the conversation for active user");
        });
        
      },
      (err) => {
        console.log("Message failed ", err);
        this.conversationService.getConversationFromId(
          this.activeUser.conversationId,
          {"assignee": this.profile.id}
        ).subscribe((conv) => {
          this.activeUser.status = 'active' // In case the conversation is already closed
          this.activeUser.messages = conv.messages;
          this.updateNewConversationList();
          this.moveUserConversationToTop(this.activeUser);
          // Clear the serach query for usability since we don';t know when to clear
          // the query since user can simply search as well but here its guranteed he/she
          // could have finalized the search and sent the message.
          // Note: This is neat since we are also resetting the filterUsers
          //       through moveUserConversationToTop
          this.searchQuery = '';

          input.value = '';
          this.scrollToBottom();
          console.log("Reloaded the conversation for active user");
        });
      }
      );
    }

    deleteSpecificConversation(convObject) {
      let foundIndex = this.users.findIndex((user) => user.id === convObject.id);
      let deletedObject = this.users.splice(foundIndex, 1);
      return deletedObject;
    }

    closeConversationVisible = false;
    openDialogForGettingClosedReason() {
      this.closeConversationVisible = true;
    }

    onClosedReasonSave() {
      this.conversationService.close(
        this.activeUser.conversationId,
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
        this.loadContacts();
        this.loadConversations()
      });
    }

    closeConversation() {
      this.openDialogForGettingClosedReason();
      
      
    }

    platform = [];
    loadRegisteredPlatforms() {
      this.platforService.getPlatforms({"organization_id": this.profile.organization}).subscribe(
        (data) => {
          this.platform = data;
        },
        (err) => {
          console.log("Compose Message | Error getting platforms ", err);  
        }
      );
    }

    selected_platform = undefined;
    onPlatformSelected() {
      console.log("selected_platform ", this.selected_platform);
    }

    newConversation() {
      let user;
      console.log("new conversation activeUser ", this.activeUser);
      this.conversationService.new(
        {
          "organization_id": this.profile.organization,
          "platform_id": this.selected_platform.id,
          "contact_id": this.activeUser.id,
          "user_id": this.profile.id
        }
      ).subscribe(
      (success_data: any) => {
          console.log(success_data.id);
          this.conversationService.getConversationFromId(
            success_data.id,
            {"assignee": this.profile.id}
          ).subscribe(
            (conv) => {
              user = {
                id: conv.contact.id,
                name: conv.contact.name,
                phone: conv.contact.phone,
                conversationId: conv.conversation_id,
                messages: conv.messages,
                img: 'http://emilcarlsson.se/assets/louislitt.png', // You can replace this with actual avatar if available
                status: conv.status,
                assignee: this.profile.id
              }
                console.log("New conversation ", user);
                this.users.unshift(user);
                this.filteredUsers = [...this.users]; // Initially display all users
                this.setUserActive(this.users[0]);
                console.log("Reloaded the conversation for active user ", this.users);
            },
            (err) => {
              this.messageService.add({ severity: 'danger', summary: 'Failed', detail: 'Conversation can not be loaded', sticky: true });
            }
          );
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'New conversation started', sticky: true });
       },
      (err) => {
        this.messageService.add({ severity: 'danger', summary: 'Failed', detail: 'New conversation can not be started', sticky: true });
      }
    );
    }

    //scrollToBottom(): void {
      //setTimeout(() => {
       // this.myScrollContainer.nativeElement.scrollTop = this.myScrollContainer.nativeElement.scrollHeight;
      //}, 0);
    //}

    get isWorkedBySomeone() {
      return this.activeUser.assignee !== this.profile.id && this.activeUser.assignee !== -1//new status; 
    }

    confirmAssignment(event: Event) {
      this.confirmationService.confirm({
          target: event.target as EventTarget,
          message: 'Are you sure you want to proceed?',
          icon: 'pi pi-exclamation-triangle',
          rejectButtonProps: {
              label: 'Cancel',
              severity: 'secondary',
              outlined: true
          },
          acceptButtonProps: {
              label: 'Save'
          },
          accept: () => {
            this.assignConversation();
          },
          reject: () => {
              this.messageService.add({ severity: 'error', summary: 'Rejected', detail: 'You have rejected', life: 3000 });
          }
      });
   }

    assignConversation() {
      this.conversationService.assign(
        this.activeUser.conversation_id,
        {'id': this.profile.id}
      ).subscribe((data) => {
        // TODO: This can be enhanced since this may not be a better way tom deal with this.
        // Can not emit assignment change event since 'New' tab component would endup in deadlock
        // and hence emitting new conversation event.
        this.assignmentEventService.emitNewConversation("New Assignment");
        // This is safe emit since "active conversation" and "chat window" are the subscribers but they is no deadlock situation.
        this.assignmentEventService.emitAssignmentChange("Assignment Change");
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Assignment successful' });
      },
      (err) => {
        console.log("List conversation | Error assigning task ", err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while assigning task', sticky: true });
      }
      );
    }

    confirmReAssignment(event: Event) {
      this.confirmationService.confirm({
          target: event.target as EventTarget,
          message: 'Are you sure you want to proceed?',
          icon: 'pi pi-exclamation-triangle',
          rejectButtonProps: {
              label: 'Cancel',
              severity: 'secondary',
              outlined: true
          },
          acceptButtonProps: {
              label: 'Save'
          },
          accept: () => {
            this.reAssignConversation();
          },
          reject: () => {
              this.messageService.add({ severity: 'error', summary: 'Rejected', detail: 'You have rejected', life: 3000 });
          }
      });
    }

    reAssignConversation() {
      console.log("this.activeUser ", this.activeUser);
      this.conversationService.assign(
        this.activeUser.conversation_id,
        {'id': this.profile.id}
      ).subscribe((data) => {
        // This is safe emit since "active conversation" and "chat window" are the subscribers but they is no deadlock situation.
        this.assignmentEventService.emitAssignmentChange("Assignment Change");
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Assignment successful' });
      },
      (err) => {
        console.log("List conversation | Error assigning task ", err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while assigning task', sticky: true });
      }
      );
    }

    ngOnDestroy(): void {
      this.messageSubscription?.unsubscribe();
      this.assignmentChangeSubscription?.unsubscribe();
    }

    
    scrollToBottom(): void {
        try {
            this.myScrollContainer.nativeElement.scrollTop = this.myScrollContainer.nativeElement.scrollHeight + 50;
        } catch(err) { }                 
    }
    

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

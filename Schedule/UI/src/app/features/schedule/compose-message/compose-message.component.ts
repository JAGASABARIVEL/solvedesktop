import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { InputGroupModule } from 'primeng/inputgroup';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { CalendarModule } from 'primeng/calendar';
import { EditorModule, EditorTextChangeEvent } from 'primeng/editor';
import { FileUploadModule } from 'primeng/fileupload';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { MessageService, PrimeNGConfig} from 'primeng/api';
import { BadgeModule } from 'primeng/badge';
import { Router } from '@angular/router';
import { BlockUIModule } from 'primeng/blockui';
import { ScheduleService } from '../../../shared/services/Schedule/schedule.service';
import { ContactService } from '../../../shared/services/Contact/contact.service';
import { GroupService } from '../../../shared/services/Group/group.service';
import { ContactModel } from '../../../shared/services/Contact/contact.model';
import { AddContactToGroupModel, CreateGroupMode } from '../../../shared/services/Group/group.model';
import { PlatformService } from '../../../shared/services/Platform/platform.service';
import { supported_contact_types, supported_frequencies, supported_datasource } from '../../../shared/services/constants';
import { ComposeMessageModel, DataSourceModel } from './compose.model';
import { ScheduleEventService } from '../../../shared/services/Events/schedule-events.service';
import { ProgressSpinnerModule } from 'primeng/progressspinner';



@Component({
  selector: 'app-compose-message',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DropdownModule,
    MultiSelectModule,
    InputGroupModule,
    ButtonModule,
    DialogModule,
    FloatLabelModule,
    CalendarModule,
    EditorModule,
    FileUploadModule,
    ProgressBarModule,
    ToastModule,
    BadgeModule,
    BlockUIModule,
    ProgressSpinnerModule
  ],
  providers: [MessageService],
  templateUrl: './compose-message.component.html',
  styleUrl: './compose-message.component.scss'
})
export class ComposeMessageComponent implements OnInit {
  
  profile!: any;
  schedule_name: string = undefined;
  blockedDocument: boolean = false;
  
  
  platform!: any;
  contact_types = supported_contact_types;
  datasource = supported_datasource;
  frequency = supported_frequencies;

  individual_contacts: any = undefined;
  selected_contacts_for_creating_group!: any;
  selected_contact_type: any = undefined;
  contacts!: any;
  selected_contacts: any = undefined;
  contact_list_placeholder!: string;
  selected_date_time: any = undefined;
  selected_frequency: any = undefined;
  selected_platform: any = undefined;
  message_text: any = undefined;
  message_typed:any = undefined;
  selected_datasource: any = undefined;
  add_contact_modal_visible = false;
  create_group_modal_visible = false;

  newGroup!: CreateGroupMode;
  newMemberToGroup!: AddContactToGroupModel;

  new_contact!: ContactModel;
  list_of_schedule_names = [];
  files = [];
  totalSize : number = 0;
  totalSizePercent : number = 0;
  excel_icon = "assets/Icons/Schedule/ms-excel.svg";

  composeMessagePayload!: ComposeMessageModel;

  constructor(
    private router: Router,
    private config: PrimeNGConfig,
    private cd: ChangeDetectorRef,
    private messageService: MessageService,
    private scheduleService: ScheduleService,
    private contactServive: ContactService,
    private groupService: GroupService,
    private platforService: PlatformService,
    private scheduleEventService: ScheduleEventService
    ) {}

  ngOnInit(): void {
    this.profile = JSON.parse(localStorage.getItem('me'));

    if (!this.profile) {
      this.router.navigate(['login']);
    }

    this.loadScheduleNames();


    this.new_contact = {
      name: "",
      phone: "",
      organization_id: this.profile.organization,
      created_by: this.profile.id
    }
    this.loadUserContacts();

    this.newGroup = {
        name: "",
        organization_id: this.profile.organization,
        created_by: this.profile.id
    }

    this.newMemberToGroup = {
        contact_id: -1,
        organization_id: this.profile.organization,
        group_id: -1
    }
    this.loadGroups();

    this.platforService.getPlatforms({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.platform = data;
      },
      (err) => {
        console.log("Compose Message | Error getting platforms ", err);  
      }
    );

  }

  onScheduleNameSelected() {
    if (this.schedule_name?.length == 0) {
      this.schedule_name = undefined;
      this.selected_contact_type = undefined;
      this.selected_contacts = undefined;
      this.selected_date_time = undefined;
      this.selected_frequency = undefined;
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
      this.message_text = undefined;
    }
    if (this.list_of_schedule_names.includes(this.schedule_name)) {
      let error = "Schedule name is already present. Please choose a different name";
      this.messageService.add({ severity: 'error', summary: 'Success', detail: error, sticky: true });
      this.schedule_name = undefined;
      this.selected_contact_type = undefined;
      this.selected_contacts = undefined;
      this.selected_date_time = undefined;
      this.selected_frequency = undefined;
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
      this.message_text = undefined;
    }
  }

  loadScheduleNames() {
    this.scheduleService.getSchedules({"organization_id": this.profile.organization}).subscribe(
      (data) => {        
        for (let schedule of data) {
            this.list_of_schedule_names.push(schedule.name);
        }
        console.log("this.list_of_schedule_names ", this.list_of_schedule_names);
      },
      (err) => {
        console.log("Compose Message | Error getting schedule names ", err);
      }
    );
  }

  loadUserContacts() {
    this.contactServive.getContacts({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.contacts = data;
        this.individual_contacts = data;
      },
      (err) => {
        console.log("Compose Message | Error getting contacts ", err);
      }
     )
  }

  loadGroups() {
    this.groupService.getGroups({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.contacts = data;
      },
      (err) => {
        console.log("Compose Message | Error getting groups ", err);
      }
     )
  }

  onContactTypeSelected() {
    this.contacts = [];
    if (this.selected_contact_type?.name == "User") {
      this.contact_list_placeholder = "Recipients";
      this.loadUserContacts();

    }
    else if (this.selected_contact_type?.name == "Group") {
      this.contact_list_placeholder = "Groups";
      this.loadGroups();
    }
    else {
      this.selected_contact_type = undefined;
      this.selected_contacts = undefined;
      this.selected_date_time = undefined;
      this.selected_frequency = undefined;
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
    }
  }

  onContactSelected() {
    if (this.selected_contacts?.length == 0) {
      // This is for hiding next element
      this.selected_contacts = undefined;
      this.selected_date_time = undefined;
      this.selected_frequency = undefined;
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
    }
  }

  onScheduleDateTimeSelected() {
    if (String(this.selected_date_time)?.length == 0) {
      this.selected_date_time = undefined;
      this.selected_frequency = undefined;
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
    }
  }

  onFrequencySelected() {
    if (String(this.selected_frequency)?.length == 0) {
      this.selected_frequency = undefined;
    }
    console.log("Selected frequence ", this.selected_frequency);
  }

  onPlatformSelected () {
    if (String(this.selected_platform)?.length == 0) {
      this.selected_platform = undefined;
      this.selected_datasource = undefined;
      this.message_text = undefined;
    }
    console.log("Selected platform ", this.selected_platform);
  }

  onMessageText(event: EditorTextChangeEvent) {
    this.message_text = event.textValue;
    console.log("onMessageText ", this.message_text);
  }

  onDatasourceSelected() {
      if (this.selected_datasource?.length <= 0) {
        this.selected_datasource = undefined;
      }
  }

  choose(event, callback) {
    callback();
}

onRemoveTemplatingFile(event, file, removeFileCallback, index) {
    removeFileCallback(event, index);
    this.totalSize -= parseInt(this.formatSize(file.size));
    this.totalSizePercent = this.totalSize / 10;
}

onClearTemplatingUpload(clear) {
    clear();
    this.totalSize = 0;
    this.totalSizePercent = 0;
}

onTemplatedUpload() {
    this.messageService.add({ severity: 'info', summary: 'Success', detail: 'File Uploaded', life: 3000 });
}

onSelectedFiles(event) {
    this.files = event.currentFiles;
    this.files.forEach((file) => {
        this.totalSize += parseInt(this.formatSize(file.size));
    });
    this.totalSizePercent = this.totalSize / 10;
    console.log("Files ", this.files);
}
uploadEvent(callback) {
    callback();
}

formatSize(bytes) {
    const k = 1024;
    const dm = 3;
    const sizes = this.config.translation.fileSizeTypes;
    if (bytes === 0) {
        return `0 ${sizes[0]}`;
    }
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const formattedSize = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));
    return `${formattedSize} ${sizes[i]}`;
}

  add_individual_contacts() {
    this.add_contact_modal_visible = false;
    this.blockedDocument = true;
    this.contactServive.createContact(this.new_contact).subscribe(
      (data) => {
        this.blockedDocument = true;
        this.cd.markForCheck();
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Contact Added' });
        this.loadUserContacts();
      },
      (err) => {
        this.blockedDocument = true;
        this.cd.markForCheck();
        this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Contact Not Added'} );
        console.log("Compose Message | Contact addition failed", err)
      }
    )
  }

  addMembers() {
    let created_contacts = 0;
    console.log("selected_contacts_for_creating_group ", this.selected_contacts_for_creating_group);
    for (let contact of this.selected_contacts_for_creating_group) {
      console.log("contact ", contact);
      this.newMemberToGroup.contact_id = contact.id;
      console.log("Contact to be added to gropup ", this.newMemberToGroup);
      this.groupService.addMembers(this.newMemberToGroup).subscribe(
        (data) => {
          console.log("Compose Message | Added member to group");
          created_contacts += 1;
          if (created_contacts == this.selected_contacts_for_creating_group.length) {
            this.blockedDocument = false;
            this.cd.markForCheck();
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Group Created and Memember Got Added' });
            this.loadGroups();
          }
          
        },
        (err) => {
            this.groupService.deleteGroup(this.newMemberToGroup).subscribe(
              () => {
                this.blockedDocument = false;
                this.cd.markForCheck();
                this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Group Member addition failed'} );
                console.log("Compose Message | Group Member addition failed", err)
                return;
              },
              (remove_group_err) => {
                this.blockedDocument = false;
                this.cd.markForCheck();
                this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Group Removal failed'} );
                console.log("Compose Message | Group Removal failed", remove_group_err);
              }
            );
        });
    }
  }

  create_group() {
    this.create_group_modal_visible = false;
    this.blockedDocument = true;

    this.groupService.createGroup(this.newGroup).subscribe(
      (data) => {
        console.log("Compose Message | Created a new group ", data);
        this.newMemberToGroup.group_id = data.id;
        this.addMembers();
      },
      (err) => {
        console.log("Compose Message | Group creation failed", err)
        this.blockedDocument = false;
        this.cd.markForCheck();
        this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Group Not Created'} );
        console.log("Compose Message | Group creation failed", err)
      }
    );
  }



  add_new_contact() {
    if (this.selected_contact_type?.name == "User") {
      this.create_group_modal_visible = false;
      this.add_contact_modal_visible = true;
    }
    else if (this.selected_contact_type?.name == "Group") {
      this.add_contact_modal_visible = false;
      this.create_group_modal_visible = true;
    }
  }

  formatDateToCustomString(date: Date): string {
    const pad = (n: number) => n.toString().padStart(2, '0');

    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1); // Months are 0-based
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    const seconds = pad(date.getSeconds());

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

  onReset() {
    this.schedule_name = undefined;
    this.selected_contact_type = undefined;
    this.selected_contacts = undefined;
    this.selected_date_time = undefined;
    this.selected_frequency = undefined;
    this.selected_platform = undefined;
    this.selected_datasource = undefined;
    this.message_text = undefined;
    this.blockedDocument = false;
  }

  onSchedule() {
    // TODO: Once the message gets scheduled
    // reset the fileds

    this.blockedDocument = true;

    

    let dataSourcePayload: DataSourceModel = {
      name: {
        type: this.selected_datasource?.name,
        file_upload: "uploaded_excel"
      }
    }

    let total_messages = 0;

    for (let contact of this.selected_contacts) {
      for (let selected_pltfrm of this.selected_platform) {
        this.composeMessagePayload = {
          name: this.schedule_name,
          uploaded_excel: this.files[0],
          organization_id: this.profile.organization,
          platform: selected_pltfrm?.id,
          user_id: this.profile.id,
          recipient_type: this.selected_contact_type?.value,
          recipient_id: contact?.id,
          message_body: this.message_text,
          scheduled_time: this.formatDateToCustomString(this.selected_date_time),
          datasource: dataSourcePayload
        }
        console.log("this.composeMessagePayload ", this.composeMessagePayload);
        this.scheduleService.createSchedule(this.composeMessagePayload).subscribe(
          (res) => {
            total_messages += 1;
            console.log("Compose Message | Schedule created ", res);
            if (total_messages == this.selected_contacts.length * this.selected_platform.length) {
              this.cd.markForCheck();
              this.scheduleEventService.emitEvent("SCHEDULED");
              this.messageService.add({ severity: 'success', summary: 'Success', detail: 'All messages Scheduled' });
              this.onReset();
            }
          },
          (err) => {
            total_messages += 1;
            this.cd.markForCheck();
            this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Error scheduling some/all messages. Please contact support team'} );
            this.onReset();
          }
        )
      }
    }
    
    
  }
}

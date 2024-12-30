import { Component, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { TableModule, Table } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ScheduleModel } from './schedule_crud.model';
import { ScheduleService } from '../../../shared/services/Schedule/schedule.service';
import { Router } from '@angular/router';
import { supported_frequencies, supported_statuses } from '../../../shared/services/constants';
import { ScheduleEventService } from '../../../shared/services/Events/schedule-events.service';
import { Subscription } from 'rxjs';
import { ToastModule } from 'primeng/toast';
import { ToolbarModule } from 'primeng/toolbar';
import { ButtonModule } from 'primeng/button';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { DialogModule } from 'primeng/dialog';
import { RadioButtonModule } from 'primeng/radiobutton';
import { StatusPipe } from '../../../shared/pipes/status.pipe';


@Component({
  selector: 'app-crud-schedules',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    ConfirmDialogModule,
    ToastModule,
    ToolbarModule,
    ButtonModule,
    TableModule,
    TagModule,
    IconFieldModule,
    InputTextModule,
    InputIconModule,
    MultiSelectModule,
    DropdownModule,
    RadioButtonModule,
    StatusPipe
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './crud-schedules.component.html',
  styleUrl: './crud-schedules.component.scss'
})
export class CrudSchedulesComponent implements OnInit, OnDestroy {
  subscription: Subscription;
  @Output() totalSchedules: EventEmitter<number> = new EventEmitter();
  totalSchedulesCount: number = 0
  profile!: any;
  customers!: any;
  schedules!: ScheduleModel[];
  schedule!: ScheduleModel;
  selectedSchedules!: ScheduleModel[];
  representatives!: any;
  
  loading: boolean = true;
  activityValues: number[] = [0, 100];
  scheduleDialog: boolean = false;
  submitted: boolean = false;
  dialogProgress: boolean = false;

  schedule_names = [];
  recipient_types = [];
  recipient_names = [];
  available_platforms = [];
  creators = [];

  frequencies = supported_frequencies;
  statuses = supported_statuses

  constructor(
    private router: Router,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private scheduleService: ScheduleService,
    private scheduleEventService: ScheduleEventService
    ) { }
  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
  ngOnInit() {

        this.profile = JSON.parse(localStorage.getItem('me'));
        if (!this.profile) {
          this.router.navigate(['login']);
        }
        this.loadSchedules();
        this.subscription = this.scheduleEventService.event$.subscribe((msg) => {
          this.loadSchedules();
        });

    this.representatives = [
        { name: 'Amy Elsner', image: 'amyelsner.png' },
        { name: 'Anna Fali', image: 'annafali.png' },
        { name: 'Asiya Javayant', image: 'asiyajavayant.png' },
        { name: 'Bernardo Dominic', image: 'bernardodominic.png' }
    ];
 }

  loadSchedules() {
    this.loading = true;
    this.totalSchedulesCount = 0;
    this.scheduleService.getSchedules({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.schedules = data
        console.log(this.schedules);
        
        for (let schedule of this.schedules) {
          this.totalSchedulesCount++;

          if (!this.schedule_names.some(schedule_name => schedule_name.value == schedule.name)) {
            this.schedule_names.push({value : schedule.name});
          }

          if (!this.recipient_types.some(rec_type => rec_type.value == schedule.recipient_type)) {
            this.recipient_types.push({value : schedule.recipient_type});
          }

          if (!this.creators.some(creator => creator.value == schedule.created_by)) {
            this.creators.push({value : schedule.created_by});
          }

          if (!this.available_platforms.some(platform => platform.value == schedule.platform_name)) {
            this.available_platforms.push({value : schedule.platform_name});
          }
          
          if (!this.recipient_names.some(recipient_name => recipient_name.value == schedule.recipient_name)) {
            this.recipient_names.push({value : schedule.recipient_name});
          }
          schedule.scheduled_time = new Date(<Date>schedule.scheduled_time);
          schedule.created_at = new Date(<Date>schedule.created_at);
      }
      this.totalSchedules.emit(this.totalSchedulesCount);
      this.loading = false;
  
      },
      (error) => {
        console.log("Error in getting schedule ", error)
        this.loading = false;
      }
    );
  }
  clear(table: Table) {
    table.clear();
  }

  getSeverity(status: string) {
    switch (status) {
        case 'Daily':
        case 'failed':
            return 'danger';
        case 'Weekly':
        case 'sent':
            return 'success';
        case 'Monthly':
        case 'scheduled':
            return 'info';
        case 'Quarterly':
        case 'cancelled':
            return 'warning';
        case 'Yearly':
            return null;
    }
    return null;
  }

  getFrequencyByName(frequency: number) {
    switch (frequency) {
        case -1:
            return 'NA';
        case 0:
            return 'Daily';
        case 1:
            return 'Weekly';
        case 2:
            return 'Monthly';
        case 3:
            return 'Quarterly';
        case 4:
            return 'Half Yearly';
        case 5:
            return 'Yearly';
    }
    return null;
  }

  onSearchInput(event: Event, dt: Table): void {
    const inputElement = event.target as HTMLInputElement;
    const searchValue = inputElement.value;
    dt.filterGlobal(searchValue, 'contains');
  }

  hideDialog() {
    this.scheduleDialog = false;
    this.submitted = false;
  }

  startSelectedSchedules() {
    this.loading = true;
    let selectedScheduleCount = 0;
    this.selectedSchedules = this.selectedSchedules.filter((schedule) => schedule.status === "cancelled" || schedule.status === "failed");
    for (let selectedSchedule of this.selectedSchedules) {
      this.scheduleService.restartSchedule(selectedSchedule.id).subscribe(
        (data) => {
          selectedScheduleCount++;
          if (selectedScheduleCount == this.selectedSchedules.length) {
            this.loadSchedules();
            this.loading = false;
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'All selected  schedules started successfully' });
          }
        },
        (error) => {
          this.selectedSchedules = null;
          this.loadSchedules();
          console.log("Error in starting schedule ", error);
          this.loading = false;
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while starting schedules', sticky: true }); 
        }
      );
    }
  }

  cancelSelectedSchedules() {
    this.loading = true;
    let selectedScheduleCount = 0;
    this.selectedSchedules = this.selectedSchedules.filter((schedule) => schedule.status === "scheduled");
    for (let selectedSchedule of this.selectedSchedules) {
      this.scheduleService.deleteSchedule(selectedSchedule.id).subscribe(
        (data) => {
          selectedScheduleCount++;
          if (selectedScheduleCount == this.selectedSchedules.length) {
            this.loadSchedules();
            this.loading = false;
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'All selected schedules cancelled successfully' });
          }
        },
        (error) => {
          this.selectedSchedules = null;
          this.loadSchedules();
          console.log("Error in deleting schedule ", error)
          this.loading = false;
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while cancelling schedule', sticky: true }); 
        }
      );
    }
  }

  cancelSelectedSchedule(schedule) {
    this.loading = true;
    this.scheduleService.deleteSchedule(schedule.id).subscribe(
      (data) => {
        this.loadSchedules();
        this.loading = false;
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Schedule cancelled successfully' });
      },
      (error) => {
        console.log("Error in deleting schedule ", error)
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while cancelling schedule', sticky: true });
      }
    );
  }

  restartSchedule(schedule) {
    this.loading = true;
    this.scheduleService.restartSchedule(schedule.id).subscribe(
      (data) => {
        this.loadSchedules();
        this.loading = false;
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Schedule restarted successfully' });
      },
      (error) => {
        console.log("Error in restarting schedule ", error)
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'An error occurred while restarting schedule', sticky: true });
      }
    );
  }

  viewSchedule(schedule) {
    this.schedule = {... schedule };
    this.scheduleDialog = true;
  }

  saveSchedule() {
    this.submitted = true;
    this.dialogProgress = true;

  }

  deleteProduct(schedule) {

  }
}

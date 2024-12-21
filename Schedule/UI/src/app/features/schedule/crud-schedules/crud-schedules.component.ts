import { Component, OnInit } from '@angular/core';
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
import { ScheduleModel } from './schedule_crud.model';
import { ScheduleService } from '../../../shared/services/Schedule/schedule.service';
import { Router } from '@angular/router';
import { supported_frequencies } from '../../../shared/services/constants';


@Component({
  selector: 'app-crud-schedules',
  standalone: true,
  imports: [
    TableModule,
    TagModule,
    IconFieldModule,
    InputTextModule,
    InputIconModule,
    MultiSelectModule,
    DropdownModule,
    HttpClientModule,
    CommonModule,
    FormsModule
  ],
  templateUrl: './crud-schedules.component.html',
  styleUrl: './crud-schedules.component.scss'
})
export class CrudSchedulesComponent implements OnInit {
  customers!: any;
  schedules!: ScheduleModel[];
  representatives!: any;
  
  loading: boolean = true;
  activityValues: number[] = [0, 100];

  schedule_names = [];
  recipient_types = [];
  recipient_names = [];
  available_platforms = [];
  creators = [];

  statuses = supported_frequencies;

  constructor(private router: Router, private scheduleService: ScheduleService) { }
  ngOnInit() {

        let organization = JSON.parse(localStorage.getItem('me'));
        if (!organization) {
          this.router.navigate(['login']);
        }
        organization = organization.organization;
        console.log("Organizations ", organization);

        this.scheduleService.getSchedules({"organization_id": organization}).subscribe(
          (data) => {
            this.schedules = data
            console.log(this.schedules);
            
            for (let schedule of this.schedules) {

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

              this.schedules.forEach((schedule) => (schedule.created_at = new Date(<Date>schedule.created_at)));
          }
          this.loading = false;
      
          },
          (error) => {
            console.log("Error in getting schedule ", error)
            this.loading = false;
          }
        );
        



    this.representatives = [
        { name: 'Amy Elsner', image: 'amyelsner.png' },
        { name: 'Anna Fali', image: 'annafali.png' },
        { name: 'Asiya Javayant', image: 'asiyajavayant.png' },
        { name: 'Bernardo Dominic', image: 'bernardodominic.png' }
    ];

 }

  clear(table: Table) {
    table.clear();
  }

  getSeverity(status: string) {
    switch (status) {
        case 'Daily':
            return 'danger';

        case 'Weekly':
            return 'success';

        case 'Monthly':
            return 'info';

        case 'Quarterly':
            return 'warning';

        case 'Yearly':
            return null;
    }
    return null;
  }

  getFrequencyByName(frequency: number) {
    switch (frequency) {
        case 0:
            return 'No';
        case 1:
            return 'Daily';
        case 2:
            return 'Weekly';
        case 3:
            return 'Monthly';
        case 4:
            return 'Quarterly';
        case 5:
            return 'Half Yearly';
        case 6:
            return 'Yearly';
    }
    return null;
  }
}

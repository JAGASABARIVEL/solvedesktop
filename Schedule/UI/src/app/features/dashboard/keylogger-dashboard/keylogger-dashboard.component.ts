import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChartModule } from 'primeng/chart';
import { DatePickerModule } from 'primeng/datepicker';
import { FloatLabelModule } from 'primeng/floatlabel';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { KeyloggerService } from '../../../shared/services/keylogger/keylogger.service';
import { OrganizationService } from '../../../shared/services/Organization/organization.service';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-keylogger-dashboard',
  imports: [
    CommonModule,
    FormsModule,

    ButtonModule,
    SelectModule,
    MultiSelectModule,
    DatePickerModule,
    ChartModule,
    FloatLabelModule,
    TableModule
  ],
  templateUrl: './keylogger-dashboard.component.html',
  styleUrl: './keylogger-dashboard.component.scss'
})
export class KeyloggerDashboardComponent implements OnInit {


  constructor(private router: Router, private organizationService: OrganizationService, private keyloggerService: KeyloggerService) {}

  profile: any;
  productivityData: any;

  employeeOptions = [];
  selectedEmployee: any = '';
  selectedDate!: Date;
  keystrokeBarChartData: any;
  appUsagePieChartData: any;
  reportSummary: any[] = [];
  chartOptions: any;
  idleTimeGaugeChartData: any;
  gaugeChartOptions: any;

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.loadUsers();
  }

  loadUsers() {
      this.organizationService.fetch_organization_by_id(this.profile.organization).subscribe((data) => {
        console.log("data ", data);
        // Populate employee options
        for (let employee of data.employees) {
          this.employeeOptions.push(
            {
              name: employee.name,
              value: employee.id
            }
          )
        }
        console.log("this.employeeOptions ", this.employeeOptions);
        this.initKeyloggerData(this.employeeOptions[0].value);
      },
      (err) => {
        console.log("Keylogger | Error getting users ", err);
      }
      );
  }

  initKeyloggerData(emp_id, selected_date=undefined) {

    let payload: any =  {
      "emp_id": emp_id,
      "organization_id": this.profile.organization,

    }
    if (selected_date != undefined) {
      payload.date = selected_date;
    }

    this.keyloggerService.get(
      payload
    ).subscribe(
      (data: any) => {
        let employees = Object.keys(data);
        console.log("Data ", data, employees)
        if (employees.length > 0) {
          this.productivityData = data;
        this.initializeData();

        //let defaultSelectedEmp = Object.keys(this.productivityData)[0];
        //let defaultSelectedDate = Object.keys(this.productivityData[defaultSelectedEmp])[0];
        //this.selectedEmployee = {"name": defaultSelectedEmp, "value": defaultSelectedEmp};
        //this.selectedDate = new Date(defaultSelectedDate);
        //this.applyFilters();
        this.initializeGaugeOptions();
        if (selected_date) {
          let required_data = data[employees[0]][selected_date];
          this.updateCharts(required_data["app_log"], required_data["total_idle_time"]);
          this.updateReport(required_data["app_log"]);
        }
        }
        }
    )
  }

  updateReport(data) {
    let localReportSummary = []
    for (let [application, keystrokes] of Object.entries(data)) {
      localReportSummary.push({"name": application, "keystrokes": keystrokes["total_key_strokes"]});
    }
    this.reportSummary = localReportSummary;
    console.log("this.reportSummary ", this.reportSummary);
  }

  initializeData(): void {

    // Populate application options
    const allApplications = new Set();
    Object.values(this.productivityData).forEach((dates: any) => {
      Object.values(dates).forEach((log: any) => {
        Object.keys(log.app_log).forEach(app => allApplications.add(app));
      });
    });

    // Chart options
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: false,  // Allows better fitting
      plugins: {
        legend: {
          display: true,
          position: 'bottom', // Moves legend below the chart instead of side
          labels: {
            font: {
              size: 12 // Reduce font size for more labels
            },
            padding: 10
          }
        },
        tooltip: {
          callbacks: {
            label: function (tooltipItem) {
              let value = tooltipItem.raw;
              return `${tooltipItem.label}: ${value} strokes`;
            }
          }
        }
      },
      layout: {
        padding: 10 // Ensures chart has enough space
      }
    };
    
  }

  formatDate(selected_date) {
    let year = selected_date.getFullYear();
    let day = selected_date.getDate();
    if (day < 10) {
      day = '0' + day;
    }
    let month = '';
    let sel_month = selected_date.getMonth() + 1
    if (sel_month >= 10) {
      month = sel_month;
    }
    else {
      month = '0' + sel_month;
    }
    return year + '-' + month + '-' + day;
  }

  applyFilters(): void {
    let selected_date_formatted = this.formatDate(new Date(this.selectedDate));
    this.initKeyloggerData(this.selectedEmployee.value, selected_date_formatted);
  }

  updateCharts(data: any, actualtotalIdleTime: number): void {
    // Bar Chart Data
    const barData = {};

    for (let [application, keystrokes] of Object.entries(data)) {
      barData[application] = keystrokes["total_key_strokes"]
    }

    //data.forEach(entry => {
    //  if (!barData[entry.application]) barData[entry.application] = 0;
    //  barData[entry.application] += entry.keystrokes;
    //});

    this.keystrokeBarChartData = {
      labels: Object.keys(barData),
      datasets: [
        {
          label: 'Keystrokes',
          data: Object.values(barData),
          backgroundColor: '#42A5F5'
        }
      ]
    };

    // Pie Chart Data
    this.appUsagePieChartData = {
      labels: Object.keys(barData),
      datasets: [
        {
          data: Object.values(barData),
          backgroundColor: ['#42A5F5', '#66BB6A', '#FFA726', '#FF6384']
        }
      ]
    };

  // Since all the records from same emploee and from same date just split based on application the idle time should be same.
  // Also convert to minutes from seconds
  const totalIdleTime = actualtotalIdleTime / 60;
  const maxIdleTime = 540 * 60; // Example max time: 9 hours which is in minutes
  const idleTimePercentage = (totalIdleTime / maxIdleTime) * 100;

  this.idleTimeGaugeChartData = {
    labels: ['Idle Time', 'Active Time'],
    datasets: [
      {
        data: [totalIdleTime, maxIdleTime - totalIdleTime],
        backgroundColor: ['#FFA726', '#42A5F5']
      }
    ]
  }
}


initializeGaugeOptions(): void {
  this.gaugeChartOptions = {
    responsive: true,
    plugins: {
      tooltip: {
        callbacks: {
          label: (tooltipItem) => `Idle Time: ${tooltipItem.raw} mins`
        }
      }
    },
    cutout: '75%', // Controls thickness of the gauge
    rotation: -90, // Starts at the top
    circumference: 180 // Semi-circle gauge
  };
}


}

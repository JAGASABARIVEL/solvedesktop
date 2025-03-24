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
import ChartDataLabels from 'chartjs-plugin-datalabels';


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

  resetData() {
    this.productivityData = []
    this.reportSummary = []
    this.keystrokeBarChartData = {}
    this.appUsagePieChartData = {}
    this.idleTimeGaugeChartData = {}
  }

  initKeyloggerData(emp_id, selected_date=undefined) {
    this.resetData();

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
          if (required_data) {
            this.updateCharts(required_data["app_log"], required_data["total_idle_time"]);
            this.updateReport(required_data["app_log"]);
          }
          else {
            this.reportSummary = []
            this.keystrokeBarChartData = {}
            this.appUsagePieChartData = {}
            this.idleTimeGaugeChartData = {}
          }
        }
        }
        }
    )
  }

  loadingReport = false;
  updateReport(data) {
    this.loadingReport = true;
    let localReportSummary = []
    for (let [application, keystrokes] of Object.entries(data)) {
      if (keystrokes["total_key_strokes"] > 0) {
        let applicationSplit = application.split("-").pop(); // Get the last part of the key
        let foundIndex = localReportSummary.findIndex((appdata)=>appdata['name'] === applicationSplit);
        if (foundIndex >= 0) {
          localReportSummary[foundIndex]["keystrokes"] += keystrokes["total_key_strokes"]
        }
        else {
          localReportSummary.push({"name": applicationSplit, "keystrokes": keystrokes["total_key_strokes"]})
        }
      }
    }
    this.reportSummary = localReportSummary;
    this.loadingReport = false;
    console.log("this.reportSummary ", this.reportSummary);
  }

  chartPlugins = [ChartDataLabels];
  initializeData(): void {

    // Populate application options
    const allApplications = new Set();
    Object.values(this.productivityData).forEach((dates: any) => {
      Object.values(dates).forEach((log: any) => {
        Object.keys(log?.app_log).forEach(app => allApplications.add(app));
      });
    });

    
    // Chart options
this.chartOptions = {
  responsive: true,
  maintainAspectRatio: false,  
  plugins: {
    legend: {
      display: true,
      position: 'bottom',
      labels: {
        font: {
          size: 12 
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
    },
    datalabels: {
      display: true, // Always show values
      color: "#000", // Make text readable
      padding: 10,  // Space between data and label
      offset: 5, // Additional offset to prevent overlap
      font: {
        weight: "bold",
        size: 12
      },
      align: 'center',  // Make sure label aligns to the center
      anchor: 'center',  // Makes the label appear inside the pie
      formatter: (value) => value // Display raw values
    }
  },
  layout: {
    padding: 10
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
      if (keystrokes["total_key_strokes"] > 0) {
        let applicationSplit = application.split("-").pop(); // Get the last part of the key
        
        // If key exists, add the value; otherwise, initialize it
        if (barData[applicationSplit]) {
          barData[applicationSplit] += keystrokes["total_key_strokes"];
        } else {
          barData[applicationSplit] = keystrokes["total_key_strokes"];
        }
      }
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
  const totalIdleTime = Math.floor(actualtotalIdleTime / 60);
  const maxIdleTime = 540; // Example max time: 9 hours which is in minutes
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
      },
      legend: {
        display: true // Hide legend for cleaner look
      },
      datalabels: {
        display: true, // Always show values
        color: "#000",
        font: {
          size: 16,
          weight: "bold"
        },
        formatter: (value) => `${value} mins`,
        anchor: "center",
        align: "center"
      }
    },
    cutout: "80%", // Adjust thickness of the gauge
    rotation: -90, // Starts from top
    circumference: 360 // Semi-circle gauge
  };


  this.gaugeChartOptions = {
  };

}  


}

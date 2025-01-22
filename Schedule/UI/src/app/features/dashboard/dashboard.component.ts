import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { DatePickerModule } from 'primeng/datepicker';
import { Subscription } from 'rxjs';
import { ConversationModel } from '../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../shared/services/Conversation/conversation.service';
import { ScheduleEventService } from '../../shared/services/Events/schedule-events.service';
import { OrganizationService } from '../../shared/services/Organization/organization.service';
import { FloatLabelModule } from 'primeng/floatlabel';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ChartModule,
    DropdownModule,
    AvatarModule,
    TableModule,
    ButtonModule,
    DatePickerModule,
    FloatLabelModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {

  profile !: any;
  periods: any[] | undefined;
  selectedConversationPerformerPeriod: any | undefined;
  selectedOrgConversationPerformerPeriod: any | undefined;
  selectedTaskPerformerInterval: any | undefined;
  conversations!: ConversationModel[];
  subscription !: Subscription;
  loadingNewConversation = false;
  selectedConversationTimePeriod = 'weekly'; // Default time period
  conversationChartData: any;
  conversationChartOptions: any;
  select_global_duration;
  selectedConversationMainPeriod;
  employees: any[];

  constructor(
    private router: Router,
    private conversationService: ConversationService,
    private conversationEventService: ScheduleEventService,
    private organizationService: OrganizationService
  ) {}
  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  ngOnInit(): void {

    this.loadProfile();

    this.periods = [
      { name: 'Daily', value: 'daily', code: '1 day'},
      { name: 'Weekly', value: 'weekly', code: '1 week' },
      { name: 'Monthly', value: 'monthly', code: '1 month' },
      { name: 'Quarterly', value: 'quarterly', code: '1 quarter' },
      { name: 'Half-yearly', value: 'half-yearly', code: 'half-year' },
      { name: 'Yearly', value: 'yearly', code: '1 year'}
    ];

    // Default duration
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    this.select_global_duration = [startOfMonth, today];

    this.selectedConversationMainPeriod = this.periods[2]; // Default selection as monthly

    this.updateChartData(); // Initialize chart data
    this.setChartOptions();
  }

  // Utility function to format the date
  formatDateToYYYYMMDD(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Month is 0-indexed
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
  }

  loadProfile() {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.loadUsers();
    this.loadConversations();
    this.subscribeForNewConversations();
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
          emp.active = 0;
          emp.closed = 0;
          emp.resolutiontime = 0;
          emp.responsetime = 0;
        }
      );
      this.loadConversationStats(); // Since its dependent on employees
    },
    (err) => {
      console.log("List conversation | Error getting users ", err);
    }
    );
  }

  subscribeForNewConversations() {
    this.subscription = this.conversationEventService.newConversationEvent$.subscribe((event)=> {
      this.loadConversations();
    });
  }

  calculateDateDifference(dateString: string): number {
    // Parse the date string into a Date object
    const receivedDate = new Date(dateString);
    // Get today's date (ignoring time)
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time to midnight for accurate day comparison
    // Calculate the difference in time (milliseconds)
    const timeDifference = today.getTime() - receivedDate.getTime();
    // Convert time difference to days
    const dayDifference = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
    return dayDifference;
  }

  loadConversations() {
    this.loadingNewConversation = true;
    this.conversationService.getAllConversations(
      {"organization_id": this.profile.organization, "conversation_status": "new"}
    ).subscribe((data) => {
      console.log("Dashboard | New conversations ", data);
      data.forEach((convers) => {
        convers.sla = this.calculateDateDifference(convers.created_at);
      })
      this.conversations = data;
      this.loadingNewConversation = false;
    },
    (err) => {
      console.log("List conversation | Error getting conversations ", err);
      this.loadingNewConversation = false;
    }
    )
  }

  /**
   * 
   * {
    "total_new": 1,
    "total_active": 4,
    "total_closed": 18,
    "customer_performance_stats": [
        {
            "contact_id": 1,
            "services_used": [
                {
                    "conversation_count": 1,
                    "platform_name": "whatsapp"
                }
            ]
        },
    ],
    "user_performance_stats": [
        {
            "total_assigned": 19,
            "total_closed": 17,
            "user_id": 1
        },
    ],
    "user_performance_stats_avg": {
        "average_resolution_rate": 0.6140350877192983,
        "average_resolution_time": 208649.00002107024,
        "average_response_time": 289608.2609564066,
        "resolution_time_per_employee": [
            {
                "avg": 367195.61334103346,
                "user_id": 1
            },
        ],
        "response_time_per_employee": [
            {
                "avg": 299791.05293133925,
                "user_id": 1
            }
        ]
    }
}
   */

  organizationConversationPerformance:any = {};
  employeeConversationPerformance:any = {};
  customerConversationPerformance:any = {};
  parseConversationStats(data) {
    this.organizationConversationPerformance.new = data.total_new;
    this.organizationConversationPerformance.active = data.total_active;
    this.organizationConversationPerformance.closed = data.total_closed;
    this.organizationConversationPerformance.resolutionrate = data.user_performance_stats_avg.average_resolution_rate;
    this.organizationConversationPerformance.resolutiontime = data.user_performance_stats_avg.average_resolution_time;
    this.organizationConversationPerformance.responsetime = data.user_performance_stats_avg.average_response_time;

    data.user_performance_stats.forEach((user_stat) => {
      let foundIndex = this.employees.findIndex((employee) => employee.id === user_stat.user_id);
      this.employees[foundIndex].active = user_stat.total_active;
      this.employees[foundIndex].closed = user_stat.total_closed;
    });

    data.user_performance_stats_avg.resolution_time_per_employee.forEach((user_stat) => {
      let foundIndex = this.employees.findIndex((employee) => employee.id === user_stat.user_id);
      this.employees[foundIndex].resolutiontime = user_stat.avg;
    });

    data.user_performance_stats_avg.response_time_per_employee.forEach((user_stat) => {
      let foundIndex = this.employees.findIndex((employee) => employee.id === user_stat.user_id);
      this.employees[foundIndex].responsetime = user_stat.avg;
    });

    console.log("organizationConversationPerformance ", this.organizationConversationPerformance);
  }

  loadConversationStats() {
    // Convert dates
    this.conversationService.stat(
      {'organization_id': this.profile.organization, 'filter': this.selectedConversationMainPeriod.value}
    ).subscribe(
      (data) => {
        this.parseConversationStats(data);
      },
      (err) => {
        console.log("Dashboard | Fetch stats ", err);
      }
    );
  }

  org_metrics_data;
  reset_org_metrics_data() {
    this.org_metrics_data = {
      labels: [],
      total: [],
      active: [],
      closed: []
    };
  }

  parseOrgMetricsData(data: any): void {
    const existingLabels = new Set(this.org_metrics_data.labels);
  
    data.org_performance_stats.forEach((org_metric) => {
      if (!existingLabels.has(org_metric.label)) {
        this.org_metrics_data.labels.push(org_metric.label);
        this.org_metrics_data.total.push(org_metric.total_assigned);
        this.org_metrics_data.active.push(org_metric.total_active);
        this.org_metrics_data.closed.push(org_metric.total_closed);
  
        existingLabels.add(org_metric.label); // Keep track of added labels
      }
    });
  }

  loadConversationOrgMetrics() {
    let globalformattedDates = this.select_global_duration.map(this.formatDateToYYYYMMDD);
    this.conversationService.orgMetrics(
      {
        'organization_id': this.profile.organization,
        'start_date': globalformattedDates[0],
        'end_date': globalformattedDates[1],
        'period': this.selectedOrgConversationPerformerPeriod.value
      }
    ).subscribe(
      (data) => {
        console.log("Dataa ", data);
        this.reset_org_metrics_data(); // Clear the existing data;
        this.parseOrgMetricsData(data);
        this.updateOrgMetricsChartData();
      },
      (err) => {

      }
    );
  }

  conversationOrgProductivityChartData;
  updateOrgMetricsChartData() {
    // Fetch and filter data based on `selectedTimePeriod`
    const data = this.org_metrics_data
    this.conversationOrgProductivityChartData = {
      labels: data.labels, // Time intervals (e.g., days, weeks)
      datasets: [
        {
          label: 'Active',
          data: data.active, // Metrics for conversations
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        },
        {
          label: 'Closed',
          data: data.closed, // Metrics for tasks closed
          backgroundColor: 'rgba(153, 102, 255, 0.6)'
        },
        {
          label: 'Total',
          data: data.total, // Metrics for tasks closed
          backgroundColor: 'rgba(180, 10, 2, 0.6)'
        }
      ]
    };
  }



  select_employee_metric;
  emp_metrics_data;
  reset_emp_metrics_data() {
    this.emp_metrics_data = {
      labels: [],
      total: [],
      active: [],
      closed: []
    };
  }
  
  parseEmployeeMetricsData(data: any): void {
    const existingLabels = new Set(this.emp_metrics_data.labels);
  
    data.user_performance_stats.forEach((user_metric) => {
      if (this.select_employee_metric.id === user_metric.assigned_user_id && 
          !existingLabels.has(user_metric.label)) {
        this.emp_metrics_data.labels.push(user_metric.label);
        this.emp_metrics_data.total.push(user_metric.total_assigned);
        this.emp_metrics_data.active.push(user_metric.total_active);
        this.emp_metrics_data.closed.push(user_metric.total_closed);
  
        existingLabels.add(user_metric.label); // Keep track of added labels
      }
    });
  }
  

  loadConversationEmploeeMetrics() {
    let globalformattedDates = this.select_global_duration.map(this.formatDateToYYYYMMDD);
    console.log(globalformattedDates);
    this.conversationService.emploeeMetrics(
      {
        'organization_id': this.profile.organization,
        'start_date': globalformattedDates[0],
        'end_date': globalformattedDates[1],
        'period': this.selectedConversationPerformerPeriod.value
      }
    ).subscribe(
      (data) => {
        console.log("Dataa ", data);
        this.reset_emp_metrics_data(); // Clear the existing data;
        this.parseEmployeeMetricsData(data);
        this.updateEmploeeMetricsChartData();
      },
      (err) => {

      }
    );
  }

  conversationEmployeeProductivityChartData;
  updateEmploeeMetricsChartData() {
    // Fetch and filter data based on `selectedTimePeriod`
    const data = this.emp_metrics_data
    this.conversationEmployeeProductivityChartData = {
      labels: data.labels, // Time intervals (e.g., days, weeks)
      datasets: [
        {
          label: 'Active',
          data: data.active, // Metrics for conversations
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        },
        {
          label: 'Closed',
          data: data.closed, // Metrics for tasks closed
          backgroundColor: 'rgba(153, 102, 255, 0.6)'
        },
        {
          label: 'Total',
          data: data.total, // Metrics for tasks closed
          backgroundColor: 'rgba(180, 10, 2, 0.6)'
        }
      ]
    };
  }

  onSelectedConversationMainIntervalChange() {
    console.log("Change in main interval");
    this.loadUsers();
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

  updateChartData() {
    // Fetch and filter data based on `selectedTimePeriod`
    const mockData = this.getMockMetrics(this.selectedConversationTimePeriod);

    this.conversationChartData = {
      labels: mockData.labels, // Time intervals (e.g., days, weeks)
      datasets: [
        {
          label: 'Conversations Closed',
          data: mockData.conversations, // Metrics for conversations
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        },
        {
          label: 'Tasks Closed',
          data: mockData.tasksClosed, // Metrics for tasks closed
          backgroundColor: 'rgba(153, 102, 255, 0.6)'
        },
      ]
    };
  }

  setChartOptions() {
    this.conversationChartOptions = {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          enabled: true
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Time Intervals'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Count'
          }
        }
      }
    };
  }

  getMockMetrics(period: string) {
    // Mock data for demonstration purposes
    switch (period) {
      case 'daily':
        return {
          labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
          conversations: [5, 8, 10, 6, 7, 12, 9],
          tasksClosed: [4, 6, 8, 5, 6, 9, 7]
        };
      case 'weekly':
        return {
          labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          conversations: [25, 40, 30, 50],
          tasksClosed: [15, 20, 35, 45]
        };
      case 'monthly':
        return {
          labels: ['January', 'February', 'March', 'April'],
          conversations: [100, 200, 150, 250],
          tasksClosed: [80, 120, 160, 220]
        };
      case 'quarterly':
        return {
          labels: ['Q1', 'Q2', 'Q3', 'Q4'],
          conversations: [400, 450, 300, 500],
          tasksClosed: [350, 400, 320, 480]
        };
      case 'half-yearly':
        return {
          labels: ['H1', 'H2'],
          conversations: [850, 1200],
          tasksClosed: [700, 1100]
        };
      case 'yearly':
        return {
          labels: ['2020', '2021', '2022', '2023'],
          conversations: [1200, 1500, 1700, 2000],
          tasksClosed: [1100, 1400, 1600, 1900]
        };
      default:
        return {
          labels: [],
          conversations: [],
          tasksClosed: []
        };
    }
  }

  

}

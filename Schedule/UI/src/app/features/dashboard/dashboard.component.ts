import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { Subscription } from 'rxjs';
import { ConversationModel } from '../../shared/services/Conversation/conversation.model';
import { ConversationService } from '../../shared/services/Conversation/conversation.service';
import { ScheduleEventService } from '../../shared/services/Events/schedule-events.service';

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
    ButtonModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {

  profile !: any;
  intervals: any[] | undefined;
  selectedConversationPerformerInterval: any | undefined;
  selectedTaskPerformerInterval: any | undefined;
  conversations!: ConversationModel[];
  subscription !: Subscription;
  loadingNewConversation = false;
  selectedConversationTimePeriod = 'weekly'; // Default time period
  conversationChartData: any;
  conversationChartOptions: any;

  constructor(
    private router: Router,
    private conversationService: ConversationService,
    private conversationEventService: ScheduleEventService
  ) {}
  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  ngOnInit(): void {

    this.loadProfile();

    this.intervals = [
      { name: 'Daily', value: 'daily' },
      { name: 'Weekly', value: 'weekly' },
      { name: 'Monthly', value: 'monthly' },
      { name: 'Quarterly', value: 'quarterly' },
      { name: 'Half-yearly', value: 'half-yearly' },
      { name: 'Yearly', value: 'yearly' }
    ];

    this.updateChartData(); // Initialize chart data
    this.setChartOptions();
  }

  loadProfile() {
    this.profile = JSON.parse(localStorage.getItem('me'));
    if (!this.profile) {
      this.router.navigate(['login']);
    }
    this.loadConversations();
    this.subscribeForNewConversations();
  }

  subscribeForNewConversations() {
    this.subscription = this.conversationEventService.newConversationEvent$.subscribe((event)=> {
      this.loadConversations();
    });
  }

  loadConversations() {
    this.loadingNewConversation = true;
    this.conversationService.getAllConversations(
      {"organization_id": this.profile.organization, "conversation_status": "new"}
    ).subscribe((data) => {
      console.log("Dashboard | New conversations ", data);
      this.conversations = data;
      this.loadingNewConversation = false;
    },
    (err) => {
      console.log("List conversation | Error getting conversations ", err);
      this.loadingNewConversation = false;
    }
    )
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
        }
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

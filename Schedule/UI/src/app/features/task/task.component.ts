import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { PanelModule } from 'primeng/panel';
import { ScrollTopModule } from 'primeng/scrolltop';
import { TabViewModule } from 'primeng/tabview';
import { TaskService } from '../../shared/services/Project/task.service';

@Component({
  selector: 'app-task',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,

    CardModule,
    PanelModule,
    BadgeModule,
    AvatarModule,
    ButtonModule,
    ScrollTopModule,
    TabViewModule,
  ],
  templateUrl: './task.component.html',
  styleUrl: './task.component.scss'
})
export class TaskComponent {

    task: any = {};
    comments: any[] = [];
    newComment: string = '';
    totalValue: number = 100; // The maximum value for the meter group
    daysSpentvalue = 10;
    overDuevalue = 0;
    daysSpentvalueStyleWidth = {width: this.daysSpentvalue + '%'}
    overDueValueStyleWidth = {width: this.overDuevalue + '%'}
    

    constructor(
      private route: ActivatedRoute,
      private taskService: TaskService
    ) {}

    ngOnInit() {
        const projectId = this.route.snapshot.params['projectId'];
        const taskId = this.route.snapshot.params['taskId'];
        this.loadTask(projectId, taskId);
        this.loadComments(projectId, taskId);
    }

    loadTask(projectId: string, taskId: string) {
        this.taskService.getTask(projectId, taskId).subscribe(
            (data) => {
              this.task = data;
              console.log("Task ", data);
            },
            (error) => console.error('Error loading task', error)
        );
    }

    loadComments(projectId: string, taskId: string) {
        this.taskService.getComments(projectId, taskId).subscribe(
            (data: any[]) => {
              this.comments = data;
              console.log("Comments ", data);
            },
            (error) => console.error('Error loading comments', error)
        );
    }

    addComment() {
        if (!this.newComment.trim()) return;
        const comment = { user_id: 1, comment_body: this.newComment }; // Replace with logged-in user
        this.taskService.addComment(this.task.projectId, this.task.id, comment).subscribe(
            () => {
                this.comments.push({ userName: 'Current User', body: this.newComment, date: new Date() });
                this.newComment = '';
            },
            (error) => console.error('Error adding comment', error)
        );
    }
  

  getPriorityColor(priority: string): string {
    switch (priority.toLowerCase()) {
        case 'high': return '#ff6f61';
        case 'medium': return '#ffb74d';
        case 'low': return '#81c784';
        default: return '#e0e0e0';
    }
  }

  viewTaskHistory(event) {

  }
  
}

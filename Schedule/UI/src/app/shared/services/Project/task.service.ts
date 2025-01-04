import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
    providedIn: 'root'
})
export class TaskService {
    private baseUrl = 'http://localhost:5000'; // Replace with actual API base URL

    constructor(private http: HttpClient) {}

    getTask(projectId: string, taskId: string) {
        return this.http.get(`${this.baseUrl}/projects/${projectId}/tasks/${taskId}`);
    }

    getComments(projectId: string, taskId: string) {
        return this.http.get(`${this.baseUrl}/projects/${projectId}/tasks/${taskId}/comment`);
    }

    addComment(projectId: string, taskId: string, comment: any) {
        return this.http.post(`${this.baseUrl}/projects/${projectId}/tasks/${taskId}/comment`, comment);
    }
}

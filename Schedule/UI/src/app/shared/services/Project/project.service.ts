import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
    providedIn: 'root'
})
export class ProjectService {
    private baseUrl = 'http://localhost:5000'; // Replace with actual API base URL

    constructor(private http: HttpClient) {}

    
}

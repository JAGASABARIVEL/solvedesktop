import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
    providedIn: 'root'
})
export class ProjectService {
    private baseUrl = 'http://localhost:5002'; // Replace with actual API base URL

    constructor(private http: HttpClient) {}

    
}

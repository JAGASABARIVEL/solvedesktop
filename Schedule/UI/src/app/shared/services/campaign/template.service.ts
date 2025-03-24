import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CampaignUrl } from '../constants';

@Injectable({
  providedIn: 'root',
})
export class TemplateService {
  private apiUrl;
  
    constructor(private http: HttpClient) {
      this.apiUrl = new CampaignUrl();
    }

  getTemplates(platform): Observable<any> {
    return this.http.get(`${this.apiUrl.templates}/${platform}`);
  }
}

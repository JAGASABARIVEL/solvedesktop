import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { OrganizationUrl } from '../constants';

@Injectable({
  providedIn: 'root'
})
export class OrganizationService {

private organizationUrl: OrganizationUrl;

  constructor(private http: HttpClient) { 
    this.organizationUrl = new OrganizationUrl();
  }

  fetch_all_organizations(): Observable<any> {
      return this.http.get(this.organizationUrl.base);
  }

}
import { HttpClient, HttpParams } from '@angular/common/http';
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

  fetch_organization_by_id(id: any): Observable<any> {
    return this.http.get(`${this.organizationUrl.base}/${id}`);
  }

  fetch_name(id:any): Observable<any> {
    return this.http.get(`${this.organizationUrl.name}/${id}`);
  }

  fetch_robo_detail(id:any): Observable<any> {
    return this.http.get(`${this.organizationUrl.base}/${id}/robo`)
  }

}
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GroupUrl } from '../constants'
import { AddContactToGroupModel, CreateGroupMode } from './group.model';

@Injectable({
  providedIn: 'root'
})
export class GroupService {

  private groupUrl;

  constructor(private http: HttpClient) { 
    this.groupUrl = new GroupUrl();
  }

  getGroups(param: any): Observable<any> {
    let httpParams = new HttpParams();
    Object.keys(param).forEach(key => {
      httpParams = httpParams.append(key, param[key].toString());
    })
    return this.http.get(this.groupUrl.fetch, {params: httpParams});
  }

  createGroup(group: CreateGroupMode): Observable<any> {
    return this.http.post(this.groupUrl.create, group);
  }

  updateGroup(groupId: number, group: any): Observable<any> {
    return this.http.put(`${this.groupUrl.update}/${groupId}`, group);
  }

  deleteGroup(payload: AddContactToGroupModel): Observable<any> {
    let httpParams = new HttpParams();
    Object.keys(payload).forEach(key => {
      httpParams = httpParams.append(key, payload[key].toString());
    })
    return this.http.delete(this.groupUrl.delete, {params: httpParams});
  }

  addMembers(payload: AddContactToGroupModel): Observable<any> {
    return this.http.post(this.groupUrl.addMembers, payload);
  }
}

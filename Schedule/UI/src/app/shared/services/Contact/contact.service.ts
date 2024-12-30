import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ContactUrl } from '../constants'
import { ContactModel } from './contact.model';

@Injectable({
  providedIn: 'root'
})
export class ContactService {

  private contactUrl;

  constructor(private http: HttpClient) {
    this.contactUrl = new ContactUrl();
   }

  getContacts(param: any): Observable<any> {
    let httpParam = new HttpParams();
    Object.keys(param).forEach(key => {
      httpParam = httpParam.append(key, param[key].toString());
    })
    return this.http.get(this.contactUrl.fetch, {params : httpParam});
  }

  createContact(payload: any): Observable<any> {
    return this.http.post(this.contactUrl.create, payload);
  }

  updateContact(contact: any): Observable<any> {
    return this.http.put(this.contactUrl.update, contact);
  }

  deleteContact(contactId: number): Observable<any> {
    return this.http.delete(`${this.contactUrl.delete}/${contactId}`);
  }

  bulkImport(organization_id: number, created_by: number, file: FormData): Observable<any> {
    return this.http.post(
      `${this.contactUrl.bulk_import}?organization_id=${organization_id}&created_by=${created_by}`,
      file);
  }
}

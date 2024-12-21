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

  createContact(payload: ContactModel): Observable<any> {
    return this.http.post(this.contactUrl.create, payload);
  }

  updateContact(contactId: number, contact: any): Observable<any> {
    return this.http.put(this.contactUrl.update, contact);
  }

  deleteContact(contactId: number): Observable<any> {
    return this.http.delete(`${this.contactUrl.delete}/${contactId}`);
  }
}

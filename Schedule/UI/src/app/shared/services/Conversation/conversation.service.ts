import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConversationUrl } from '../constants';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ConversationService {

  private conversationUrl;

  constructor(private http: HttpClient) {
    this.conversationUrl = new ConversationUrl();
  }

  getAllConversations(param: any): Observable<any> {
    let httpParams = new HttpParams();
    Object.keys(param).forEach(key => {
      httpParams = httpParams.append(key, param[key].toString());
    })
    return this.http.get(this.conversationUrl.base, { params: param });
  }

  getConversationFromId(conversationId: number): Observable<any> {
    return this.http.get(`${this.conversationUrl.base}/${conversationId}`);
  }
}
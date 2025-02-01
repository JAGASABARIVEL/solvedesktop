import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { KeyloggerUrl } from '../constants'

@Injectable({
  providedIn: 'root'
})
export class KeyloggerService {

  private keyloggerUrl: KeyloggerUrl;

  constructor(private http: HttpClient) { 
    this.keyloggerUrl = new KeyloggerUrl();
  }

  get(param: any): Observable<any> {
    let httpParams = new HttpParams();
        Object.keys(param).forEach(key => {
          httpParams = httpParams.append(key, param[key].toString());
        })
        return this.http.get(this.keyloggerUrl.base, {params: httpParams});
  }

}

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PlatformUrl } from '../constants';

@Injectable({
  providedIn: 'root'
})
export class PlatformService {

  private platformUrl;

  constructor(private http: HttpClient) { 
    this.platformUrl = new PlatformUrl();
  }

  getPlatforms(param: any): Observable<any> {
    let httpParams = new HttpParams();
    Object.keys(param).forEach(key => {
      httpParams = httpParams.append(key, param[key].toString());
    });
    return this.http.get(this.platformUrl.fetch, {params: httpParams});
  }

  createPlatform(platform: any): Observable<any> {
    return this.http.post(this.platformUrl.create, platform);
  }

  updatePlatform(platformId: number, platform: any): Observable<any> {
    return this.http.put(`${this.platformUrl.update}/${platformId}`, platform);
  }

  deletePlatform(platformId: number): Observable<any> {
    return this.http.delete(`${this.platformUrl.delete}/${platformId}`);
  }
}

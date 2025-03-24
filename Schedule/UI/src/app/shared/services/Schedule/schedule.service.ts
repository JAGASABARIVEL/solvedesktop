import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ScheduleUrl } from '../constants';
import { ComposeMessageModel } from '../../../features/schedule/compose-message/compose.model';

@Injectable({
  providedIn: 'root'
})
export class ScheduleService {

  private scheduleUrl;

  constructor(private http: HttpClient) {
    this.scheduleUrl = new ScheduleUrl();
  }

  private convertToFormData(schedule: ComposeMessageModel): FormData {
    const formData = new FormData();
    formData.append('name', schedule.name);
    formData.append('uploaded_excel', schedule.uploaded_excel); // File object
    formData.append('organization_id', schedule.organization_id.toString());
    formData.append('platform', schedule.platform.toString());
    formData.append('user_id', schedule.user_id.toString());
    formData.append('recipient_type', schedule.recipient_type);
    formData.append('recipient_id', schedule.recipient_id.toString());
    formData.append('message_body', schedule.message_body);
    formData.append('scheduled_time', schedule.scheduled_time);
    formData.append('template', schedule.template);

    // Handle nested object (datasource)
    formData.append('datasource', JSON.stringify(schedule.datasource));
    return formData;
  }

  getSchedules(param: any): Observable<any> {
    let httpParam = new HttpParams();
    Object.keys(param).forEach(key => {
      httpParam = httpParam.append(key, param[key].toString());
    })
    return this.http.get(this.scheduleUrl.fetch, {params : httpParam});
  }

  createSchedule(schedule: any): Observable<any> {
    console.log("schedule ", schedule)
    const formData = this.convertToFormData(schedule);
    return this.http.post(this.scheduleUrl.create, formData);
  }

  updateSchedule(scheduleId: number, schedule: any): Observable<any> {
    return this.http.put(`${this.scheduleUrl.update}/${scheduleId}`, schedule);
  }

  deleteSchedule(scheduleId: number): Observable<any> {
    return this.http.delete(`${this.scheduleUrl.delete}/${scheduleId}`);
  }

  restartSchedule(scheduleId: number) {
    return this.http.put(`${this.scheduleUrl.restart}/${scheduleId}`, {});
  }

  getHistory(organization_id: number): Observable<any> {
    const httpParams = new HttpParams().set('organization_id', organization_id.toString());
    return this.http.get(this.scheduleUrl.history, {params: httpParams});
  }
}

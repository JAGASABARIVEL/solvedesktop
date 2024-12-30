import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ScheduleEventService {
    private eventSubject = new Subject<any>();
    event$ = this.eventSubject.asObservable();

    emitEvent(message: any) {
        this.eventSubject.next(message);
    }
}
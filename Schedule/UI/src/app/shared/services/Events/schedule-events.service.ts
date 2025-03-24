import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ScheduleEventService {
    private eventSubject = new Subject<any>();
    private eventAssignmentSubject = new Subject<any>();
    private eventNewConversationSubject = new Subject<any>();
    private eventCloseConversationSubject = new Subject<any>();

    event$ = this.eventSubject.asObservable();
    assignmentEvent$ = this.eventAssignmentSubject.asObservable();
    newConversationEvent$ = this.eventNewConversationSubject.asObservable();
    closeConversationEvent$ = this.eventCloseConversationSubject.asObservable();



    emitEvent(message: any) {
        this.eventSubject.next(message);
    }

    emitAssignmentChange(message: any) {
      this.eventAssignmentSubject.next(message);
    }

    emitNewConversation(message: any) {
      this.eventNewConversationSubject.next(message);
    }

    emitCloseConversation(message: any) {
      this.eventCloseConversationSubject.next(message);
    }


}
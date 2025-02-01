import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'complete_status',
  standalone: true
})
export class StatusPipe implements PipeTransform {

  transform(value: string): string {
    switch(value) {
      case "scheduled":
        return "Scheduled"
      case "sent":
        return "Completed"
      case "failed":
        return "Error"
      case "in-progress":
        return "Stuck IO"
      case "partially_failed":
        return "Partial Errors"
      default:
        return value
    }
  }
}

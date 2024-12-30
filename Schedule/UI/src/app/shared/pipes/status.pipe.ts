import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'complete_status',
  standalone: true
})
export class StatusPipe implements PipeTransform {

  transform(value: string): string {
    return value === "sent" ? "Completed" : value;
  }

}

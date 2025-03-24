import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'performJsonOp'
})
export class PerformJsonOpPipe implements PipeTransform {

  transform(value: any, op: string): any {
    switch(op) {
      case "dump":
        return JSON.stringify(value)
      case "load":
        return JSON.parse(value);
    }
  }
}

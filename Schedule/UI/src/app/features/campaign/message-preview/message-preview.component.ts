import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-message-preview',
  standalone: true,
  imports: [
    CommonModule,
    CardModule
  ],
  templateUrl: './message-preview.component.html',
  styleUrl: './message-preview.component.scss'
})
export class MessagePreviewComponent {

  _selectedTemplateForPreview;

  @Input()
    set selectedTemplateForPreview(value: any) {
      if (typeof value === 'string') {
        value = JSON.parse(value);
      }
      if (value !== undefined) {
        this._selectedTemplateForPreview = value;
        console.log("value ", value);
      }
    }
  
    get selectedTemplateForPreview(): any {
      return this._selectedTemplateForPreview;
    }

}

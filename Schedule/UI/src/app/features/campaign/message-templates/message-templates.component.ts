import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CardModule } from 'primeng/card';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FloatLabelModule } from 'primeng/floatlabel';
import { SelectModule } from 'primeng/select';
import { TemplateService } from '../../../shared/services/campaign/template.service';
import { MessagePreviewComponent } from '../message-preview/message-preview.component';

@Component({
  selector: 'app-message-templates',
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    SelectModule,
    CardModule,
    FloatLabelModule,

    MessagePreviewComponent
  ],
  templateUrl: './message-templates.component.html',
  styleUrl: './message-templates.component.scss'
})
export class MessageTemplatesComponent implements OnInit {

  _selectedPlatform: any;
  @Output() selectTemplate: EventEmitter<any> = new EventEmitter();

  templates;
  
  selectedTemplate: any = null;

  constructor(private campaignService: TemplateService) {}


  ngOnInit(): void {    
  }


  @Input()
  set selectedPlatform(value: string) {
    this._selectedPlatform = value;
    this.handleSelectedPlatformChange(value);
  }

  get selectedPlatform(): string {
    return this._selectedPlatform;
  }

  handleSelectedPlatformChange(newValue: any) {
    console.log('Handling data change:', newValue, newValue.id);
    this.campaignService.getTemplates(newValue?.id).subscribe((templates_list) => {
      // At this moment we support only whatsapp
      this.templates = templates_list["whatsapp"];
      console.log("this.templates ", this.templates);
      //this.templates.unshift(
      //  {
      //    name: 'None'
      //  }
      //)
    })
  }

  onTemplateSelect(templateName: string) {
    console.log("onTemplateSelect ", templateName);
    this.selectedTemplate = this.templates.find(t => t.name === templateName);
    if (!this.selectedTemplate || this.selectedTemplate?.name === 'None' ) {
      this.selectedTemplate = undefined;
    }
    this.selectTemplate.emit(this.selectedTemplate);
  }
}

import { Component, OnInit } from '@angular/core';
import { TableModule, Table } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { HttpClientModule } from '@angular/common/http';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
@Component({
  selector: 'app-message-history',
  standalone: true,
  imports: [
    TableModule,
    TagModule,
    IconFieldModule,
    InputTextModule,
    InputIconModule,
    MultiSelectModule,
    DropdownModule,
    HttpClientModule,
    CommonModule,
    FormsModule
  ],
  templateUrl: './message-history.component.html',
  styleUrl: './message-history.component.scss'
})
export class MessageHistoryComponent implements OnInit {
    messages!:any;
    loading: boolean = true;

    constructor() {}
  ngOnInit(): void {
    this.messages = [
      {
        "name": "Saroja",
        "schedule": "GST-2024",
        "status": "Active"
      },
      {
        "name": "Karunanithi",
        "schedule": "GST-2025",
        "status": "Active"
      },
      {
        "name": "Piraikadir",
        "schedule": "GST-2026",
        "status": "Active"
      },
      {
        "name": "Shwetha",
        "schedule": "GST-2027",
        "status": "Active"
      },
      {
        "name": "Jagasabarivel",
        "schedule": "GST-2028",
        "status": "Active"
      }
    ]
    this.loading = false;
  }

}

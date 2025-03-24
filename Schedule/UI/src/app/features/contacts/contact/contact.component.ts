import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { ConfirmationService, MessageService } from 'primeng/api';
//import { Product } from '@domain/product';
//import { ProductService } from '@service/productservice';
import { Table, TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { RippleModule } from 'primeng/ripple';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { ToolbarModule } from 'primeng/toolbar';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { CommonModule } from '@angular/common';
import { FileUploadModule } from 'primeng/fileupload';
import { DropdownModule } from 'primeng/dropdown';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TagModule } from 'primeng/tag';
import { RadioButtonModule } from 'primeng/radiobutton';
import { AvatarModule } from 'primeng/avatar';
import { FormsModule } from '@angular/forms';
import { ContactModel } from './contacts.model';
import { ContactService } from '../../../shared/services/Contact/contact.service';
import { Router } from '@angular/router';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    DialogModule,
    RippleModule,
    ButtonModule,
    ToastModule,
    ToolbarModule,
    ConfirmDialogModule,
    TextareaModule,
    FileUploadModule,
    DropdownModule,
    TagModule,
    RadioButtonModule,
    InputTextModule,
    AvatarModule,
    ProgressSpinnerModule,

    InputGroupModule,
    InputGroupAddonModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './contact.component.html',
  styleUrl: './contact.component.scss'
})
export class ContactComponent {

  @Output() totalContacts: EventEmitter<number> = new EventEmitter();

  profile!: any;
  loading = true;
  dialogProgress = false;
  productDialog: boolean = false;
  products!: ContactModel[];
  product!: any;
  selectedProducts!: any[] | null;
  submitted: boolean = false;
  statuses!: any[];
  constructor(private router: Router, private messageService: MessageService, private confirmationService: ConfirmationService, private contactService: ContactService) {}
  ngOnInit() {

    this.profile = JSON.parse(localStorage.getItem('me'));

    if (!this.profile) {
      this.router.navigate(['login']);
    }

    this.loadContacts();

    this.statuses = [
        { label: 'INSTOCK', value: 'instock' },
        { label: 'LOWSTOCK', value: 'lowstock' },
        { label: 'OUTOFSTOCK', value: 'outofstock' }
    ];
    this.loading = false;
  }

  loadContacts() {
    this.loading = true;
    this.contactService.getContacts({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.loading = false;
        this.products = data;
        this.totalContacts.emit(this.products.length);
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Contacts Loaded', life: 3000 });
      },
      (err) => {
        this.loading = false;
        console.log("Contacts | Error getting contacts ", err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Contacts Not Loaded', sticky: true });
      }
    );
  }

  onSearchInput(event: Event, dt: Table): void {
    const inputElement = event.target as HTMLInputElement;
    const searchValue = inputElement.value;
    dt.filterGlobal(searchValue, 'contains');
  }

  openNew() {
    this.product = {};
    this.submitted = false;
    this.productDialog = true;
}

  deleteSelectedProducts() {
    this.confirmationService.confirm({
        message: 'Are you sure you want to delete the selected contacts?',
        header: 'Confirm',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
            this.loading = true;
            let selectedProductsCount = 0;
            for (let contact of this.selectedProducts) {
              this.contactService.deleteContact(contact.id).subscribe(
                (data) => {
                  selectedProductsCount += 1;
                  this.products = this.products.filter((val) => val.id !== contact.id);
                  if (selectedProductsCount === this.selectedProducts.length) {
                    this.selectedProducts = null;
                    this.loading = false;
                    this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Products Deleted', life: 3000 });
                  }
                },
                (err) => {
                  this.selectedProducts = null;
                  this.loading = false;
                  console.log("Error deleting contact ", err);
                  this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Contact Not Deleted', sticky: true });
                }
              );
            }
        }
    });
  }

  editProduct(product: any) {
    this.product = { ...product };
    this.productDialog = true;
  }

  deleteProduct(product: any) {
    this.confirmationService.confirm({
        message: 'Are you sure you want to delete ' + product.name + '?',
        header: 'Confirm',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
            this.loading = true;
            this.contactService.deleteContact(product.id).subscribe(
              (data) => {
                this.products = this.products.filter((val) => val.id !== product.id);
                this.product = {};
                this.loading = false;
                this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Contact Deleted', life: 3000 });
              },
              (err) => {
                console.log("Contacts | Error deleting contact ", err);
                this.loading = false;
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Contact Not Deleted', sticky: true });
              }
            );
        }
    });
  }

  hideDialog() {
    this.productDialog = false;
    this.submitted = false;
  }

  saveProduct() {
    this.submitted = true;
    this.dialogProgress = true;

    if (this.product.name?.trim()) {
        if (this.product.id) {
            this.contactService.updateContact(this.product).subscribe(
              (data) => {
                this.products[this.findIndexById(this.product.id)] = this.product;
                this.products = [...this.products];
                this.product = {};
                this.dialogProgress = false;
                this.productDialog = false;
                this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Contact Updated', life: 3000 });
              },
              (err) => {
                console.log("Contacts | Error updating contact ", err);
                this.product = {};
                this.dialogProgress = false;
                this.productDialog = false;
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Contact Not Updated', sticky: true });
              }
            );
        } else {
            this.product.organization_id = this.profile.organization;
            this.product.created_by = this.profile.id;
            this.contactService.createContact(this.product).subscribe(
              (data) => {
                this.product.id = data.id;
                this.products.push(this.product);
                this.dialogProgress = false;
                this.productDialog = false;
                this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Contact Created', life: 3000 });
              },
              (err) => {
                console.log("Contacts | Error creating contact ", err);
                this.product = {};
                this.dialogProgress = false;
                this.productDialog = false;
                this.messageService.add({ severity: 'error', summary: 'Error', detail: err?.error?.error, sticky: true });
              }
            );
        }
    }
  }

  findIndexById(id: string): number {
    let index = -1;
    for (let i = 0; i < this.products.length; i++) {
        if (this.products[i].id === id) {
            index = i;
            break;
        }
    }

    return index;
  }

  createId(): string {
    let id = '';
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (var i = 0; i < 5; i++) {
        id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return id;
  }

  getSeverity(status: string) {
    switch (status) {
        case 'Individual':
            return 'info';
        case 'Micro Enterprise':
            return 'success';
        case 'Small Enterprise':
            return 'warn';
        case 'Medium Enterprise':
            return 'danger';
    }
    return 'danger';
  }

  onBulkUpload(event: any, fileUpload: any): void {
    console.log("onBulkUpload ", event.files);
    this.loading = true;
    const file = event.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        this.contactService.bulkImport(
          this.profile.organization,
          this.profile.id,
          formData
        ).subscribe({
            next: (response: any) => {
                this.loadContacts();
                this.messageService.add({ 
                    severity: 'success', 
                    summary: 'Import Successful', 
                    detail: 'contacts imported successfully', 
                    sticky: true
                });
                fileUpload.clear()
                this.loading = false;
            },
            error: (err) => {
                this.messageService.add({ 
                    severity: 'error', 
                    summary: 'Import Failed', 
                    detail: 'An error occurred while importing contacts.', 
                    sticky: true
                });
                fileUpload.clear()
                this.loading = false;
            }
        });
    }
}

showAddContactDialog() {

}
}

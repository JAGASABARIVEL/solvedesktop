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
import { Router } from '@angular/router';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { GroupModel } from './groups.model';
import { GroupService } from '../../../shared/services/Group/group.service';
import { AddContactToGroupModel } from '../../../shared/services/Group/group.model';
import { ContactService } from '../../../shared/services/Contact/contact.service';
import { MultiSelectModule } from 'primeng/multiselect';
import { group } from '@angular/animations';

@Component({
  selector: 'app-groups',
  templateUrl: './groups.component.html',
  styleUrl: './groups.component.scss',
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
    MultiSelectModule,

    InputGroupModule,
    InputGroupAddonModule
  ],
  providers: [MessageService, ConfirmationService],
})
export class GroupsComponent {

  @Output() totalGroups: EventEmitter<number> = new EventEmitter();

  profile!: any;
  loading = true;
  dialogProgress = false;
  productDialog: boolean = false;
  products!: GroupModel[];
  product!: any;
  selectedProducts!: any[] | null;
  submitted: boolean = false;
  statuses!: any[];
  constructor(
    private router: Router,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private contactService: ContactService,
    private groupService: GroupService) {}
  ngOnInit() {

    this.profile = JSON.parse(localStorage.getItem('me'));

    if (!this.profile) {
      this.router.navigate(['login']);
    }

    this.loadUserContacts();
    this.loadContactGroups();
    this.loading = false;
  }

  validateGroupName() {
    let groupNames = [];
    this.products.forEach((prod) => {
      groupNames.push(prod.name);
    });
    if (groupNames.includes(this.product.name)) {
      this.product = {};
      let error = "Group name is already present. Please choose a different name";
      this.messageService.add({ severity: 'error', summary: 'Success', detail: error, sticky: true });
    }
  }

  individual_contacts !: any;
  loadUserContacts() {
    this.contactService.getContacts({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.individual_contacts = data;
        this.individual_contacts.forEach((individual_contact)=> {
          individual_contact.name = individual_contact.name === ''? individual_contact.phone : individual_contact.name;
        })
      },
      (err) => {
        console.log("Compose Message | Error getting contacts ", err);
      }
     )
  }

  loadContactGroups() {
    this.loading = true;
    this.groupService.getGroups({"organization_id": this.profile.organization}).subscribe(
      (data) => {
        this.loading = false;
        this.products = data;
        console.log("Contact Groups ", data);
        this.totalGroups.emit(this.products.length);
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Groups Loaded', life: 3000 });
      },
      (err) => {
        this.loading = false;
        console.log("Contacts | Error getting contacts ", err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Groups Not Loaded', sticky: true });
      }
    );
  }

  onSearchInput(event: Event, dt: Table): void {
    const inputElement = event.target as HTMLInputElement;
    const searchValue = inputElement.value;
    dt.filterGlobal(searchValue, 'contains');
  }

  onSearchMemeberInput(event: Event, dt: Table): void {
    const inputElement = event.target as HTMLInputElement;
    const searchValue = inputElement.value;
    dt.filterGlobal(searchValue, 'contains');
  }

  members_not_part_of_this_group;
  openNew() {
    this.product = {};
    this.members_not_part_of_this_group = this.individual_contacts;
    this.submitted = false;
    this.productDialog = true;
  }

  async deleteSelectedProducts(): Promise<void> {
    for (let product of this.selectedProducts) {
      await this.deleteProduct(product); // Await each deletion sequentially
    }
  }

  async deleteProduct(product: any): Promise<void> {
    const isConfirmed = await this.confirmDeletion(product);
    if (!isConfirmed) {
      return; // Exit if the user cancels the confirmation
    }
    this.loading = true;
    product.group_id = product.id;
    console.log('Deleting product:', product);
    try {
      await this.groupService.deleteGroup(product).toPromise(); // Await the deletion API call
      this.products = this.products.filter((val) => val.id !== product.id);
      this.messageService.add({
        severity: 'success',
        summary: 'Successful',
        detail: 'Group Deleted',
        life: 3000,
      });
    } catch (err) {
      console.error('Groups | Error deleting group:', err);
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Group Not Deleted',
        sticky: true,
      });
    } finally {
      this.loading = false;
    }
  }

  confirmDeletion(product: any): Promise<boolean> {
    return new Promise((resolve) => {
      this.confirmationService.confirm({
        message: 'Are you sure you want to delete ' + product.name + '?',
        header: 'Confirm',
        icon: 'pi pi-exclamation-triangle',
        accept: () => resolve(true),   // Resolve promise when user accepts
        reject: () => resolve(false), // Resolve promise when user rejects
      });
    });
  }
  

  hideDialog() {
    this.productDialog = false;
    this.submitted = false;
  }

  editProduct(product: any) {
    this.product = { ...product };
    this.members_not_part_of_this_group = this.individual_contacts.filter((individual_contact) => !this.product.members.some((actual_member => individual_contact.phone === actual_member.contact_phone)))
    this.productDialog = true;
  }

  refreshMemebersContactList() {
    this.selected_contacts_for_creating_group = [];
    this.members_not_part_of_this_group = this.individual_contacts.filter((individual_contact) => !this.product.members.some((actual_member => individual_contact.phone === actual_member.contact_phone)))
  }
  
  add_members_modal_visible = false;
  selected_contacts_for_creating_group !: any;
  newMemberToGroup!: AddContactToGroupModel;

  async addMemebersToExistingGroup(patch=false) {
    this.newMemberToGroup = {
      contact_id: -1,
      organization_id: this.profile.organization,
      group_id: this.product.id
    }
    let created_contacts = 0;

    // Handle if there are no members selected for new or all members unselected in existing groups.
    if (!this.product.members || this.product.members?.length === 0) {
      if (patch) {
        this.groupService.patchGroupDetails(this.product).subscribe(
          (data) => {
            this.product.total = this.product.members.length;
            this.products[this.findIndexById(this.product.id)] = this.product;
            this.products = [...this.products];
            this.product = {};
            this.dialogProgress = false;
            this.productDialog = false;
            this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Group Updated', life: 3000 });
          },
          (err) => {
            console.log("Groups | Error updating group ", err);
            this.product = {};
            this.dialogProgress = false;
            this.productDialog = false;
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Group Not Updated', sticky: true });
          }
        );
      }
      else {
        this.product.members = []; // This would initialize members if empty group is selected which would help while editing.
        this.product.total = this.product.members.length;
        this.products.push(this.product);
        console.log("New products update ", this.products);
        this.dialogProgress = false;
        this.productDialog = false;
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Group Created', life: 3000 });
      }
    }
    else {
      for (let contact of this.product.members) {
        this.newMemberToGroup.contact_id = contact.contact_id;
        // New group would not be having 'group_id' initialized
        this.newMemberToGroup.group_id = this.product.id;
        this.groupService.addMembers(this.newMemberToGroup).subscribe(
          (data) => {
            created_contacts += 1;
            let foundIndex =  this.product.members.findIndex((member) => member.contact_id === contact.contact_id)
            this.product.members[foundIndex].id = data.member_id;
            if (created_contacts == this.product.members.length) {
              this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Memember Got Added' });
              if (patch) {
                    this.groupService.patchGroupDetails(this.product).subscribe(
                      (data) => {
                        this.product.total = this.product.members.length;
                        this.products[this.findIndexById(this.product.id)] = this.product;
                        this.products = [...this.products];
                        this.product = {};
                        this.dialogProgress = false;
                        this.productDialog = false;
                        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Group Updated', life: 3000 });
                      },
                      (err) => {
                        console.log("Groups | Error updating group ", err);
                        this.product = {};
                        this.dialogProgress = false;
                        this.productDialog = false;
                        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Group Not Updated', sticky: true });
                      }
                    );
              }
              else {
                this.product.total = this.product.members.length;
                this.products.push(this.product);
                console.log("New products update ", this.products);
                this.dialogProgress = false;
                this.productDialog = false;
                this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Group Created', life: 3000 });
              }
            }
          },
          (err) => {
              this.messageService.add( { severity: 'error', summary: 'Error', detail: 'Group Member addition failed'} );
              console.log("Manage Groups | Group Member addition failed", err)
          });
      }
    }


    
    
  }


  addMembers() {
    if (this.product.id) {
      const temp = this.product.members;
      this.product.members = [];
      for (let temp_existing_contact of temp) {
        this.product.members.push(temp_existing_contact);
      }
      for (let contact of this.selected_contacts_for_creating_group) {
        this.product.members.push({'contact_id': contact.id, 'contact_name': contact.name, 'contact_phone': contact.phone});
      }      
      this.product.members = this.product.members;
    }
    else {
      this.product.members = [];
      // Do not do anything unless group is created.
      for (let contact of this.selected_contacts_for_creating_group) {
        this.product.members.push({'contact_id': contact.id, 'contact_name': contact.name, 'contact_phone': contact.phone});
      }
    }
    this.refreshMemebersContactList();
    this.add_members_modal_visible = false;
  }

  async saveSelectedProduct() {
    try {
      this.selected_contacts_for_creating_group = [];
      await this.addMemebersToExistingGroup(true);
    }
    catch (err) {
      console.log("Groups | Error updating group ", err);
    }
  }

  async saveNewProduct() {
    this.product.organization_id = this.profile.organization;
    this.product.created_by = this.profile.id;
    this.groupService.createGroup(this.product).subscribe(
      (data) => {
        this.product.id = data.id;
        this.totalGroups.emit(this.products.length);
        this.addMemebersToExistingGroup();
      },
      (err) => {
        console.log("Groups | Error creating Group ", err);
        this.product = {};
        this.dialogProgress = false;
        this.productDialog = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Group Not Created', sticky: true });
      }
    );
  }

  async saveProduct() {
    this.submitted = true;
    this.dialogProgress = true;
    if (this.product.id) {
      await this.saveSelectedProduct();
    }
    else {
      console.log("product ", this.product);
      await this.saveNewProduct();
    }
  }

  findIndexById(id: any): number {
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

  }

showAddContactDialog() {

}
}

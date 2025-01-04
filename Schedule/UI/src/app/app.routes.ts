import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/app.layout.component';
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';

export const routes: Routes = [
    {
        path: '', component: AppLayoutComponent,
        children: [
            { path: '', loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent) },
            { path: 'schedule', loadComponent: () => import('./features/schedule/schedule.component').then(m => m.ScheduleComponent) },
            { path: 'contacts', loadComponent: () => import('./features/contacts/contacts.component').then(m => m.ContactsComponent) },
            { path: 'chat', loadComponent: () => import('./features/chat/chat.component').then(m => m.ChatComponent) },
            { path: 'me', loadComponent: () => import('./auth/user-profile/user-profile.component').then(m => m.UserProfileComponent) },
        ]
    },
    { path: 'login', component: LoginComponent },
    { path: 'signup', component: SignupComponent },
];
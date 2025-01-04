import { RouterModule } from '@angular/router';
import { Component, NgModule } from '@angular/core';
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';
import { AppLayoutComponent } from './layout/app.layout.component';


@NgModule({
    imports: [
        RouterModule.forRoot([
            {
                path: '', component: AppLayoutComponent,
                children: [
                    { path: '', loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent) },
                    { path: 'schedule', loadComponent: () => import('./features/schedule/schedule.component').then(m => m.ScheduleComponent) },
                    { path: 'contacts', loadComponent: () => import('./features/contacts/contacts.component').then(m => m.ContactsComponent) },
                    { path: 'chat', loadComponent: () => import('./features/chat/chat.component').then(m => m.ChatComponent) },
                    { path: 'projects/:projectId/tasks/:taskId', loadComponent: () => import('./features/task/task.component').then(m => m.TaskComponent) },
                    { path: 'me', loadComponent: () => import('./auth/user-profile/user-profile.component').then(m => m.UserProfileComponent) },
                ]
            },
            { path: 'login', component: LoginComponent },
            { path: 'signup', component: SignupComponent },
            

            //{ path: 'notfound', component: NotfoundComponent },
            //{ path: '**', redirectTo: '/notfound' },
        ], { scrollPositionRestoration: 'enabled', anchorScrolling: 'enabled', onSameUrlNavigation: 'reload' })
    ],
    exports: [RouterModule]
})
export class AppRoutingModule {
}

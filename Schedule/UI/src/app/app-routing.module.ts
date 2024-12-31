import { RouterModule } from '@angular/router';
import { Component, NgModule } from '@angular/core';
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';
import { AppLayoutComponent } from './layout/app.layout.component';
import { ScheduleComponent } from './features/schedule/schedule.component';
import { ComposeMessageComponent } from './features/schedule/compose-message/compose-message.component';
import { CrudSchedulesComponent } from './features/schedule/crud-schedules/crud-schedules.component';
import { UserProfileComponent } from './auth/user-profile/user-profile.component';
import { ContactsComponent } from './features/contacts/contacts.component';
import { ChatComponent } from './features/chat/chat.component';

@NgModule({
    imports: [
        RouterModule.forRoot([
            {
                path: '', component: AppLayoutComponent,
                children: [
                    { path: 'schedule', loadComponent: () => import('./features/schedule/schedule.component').then(m => m.ScheduleComponent) },
                    { path: 'contacts', loadComponent: () => import('./features/contacts/contacts.component').then(m => m.ContactsComponent) },
                    { path: 'chat', loadComponent: () => import('./features/chat/chat.component').then(m => m.ChatComponent) },
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

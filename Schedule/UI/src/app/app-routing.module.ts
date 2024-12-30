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

@NgModule({
    imports: [
        RouterModule.forRoot([
            {
                path: '', component: AppLayoutComponent,
                children: [
                    { path: 'schedule',  component: ScheduleComponent},
                    { path: 'contacts',  component: ContactsComponent},
                    { path: 'me', component: UserProfileComponent}
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

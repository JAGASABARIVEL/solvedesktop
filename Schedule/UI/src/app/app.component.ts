import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AvatarModule } from 'primeng/avatar';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    AvatarModule
  ],
  templateUrl: './app.component.html'
})
export class AppComponent {
}
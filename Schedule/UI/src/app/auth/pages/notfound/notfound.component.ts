import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-notfound',
  imports: [RouterModule, ButtonModule, CardModule],
  templateUrl: './notfound.component.html',
  styleUrl: './notfound.component.scss',
  standalone: true,
})
export class NotfoundComponent {

}
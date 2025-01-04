import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import {  } from './app/layout/app.layout.component';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
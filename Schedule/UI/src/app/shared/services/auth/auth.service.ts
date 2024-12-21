import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthUrl } from '../constants'
import { EmployeeSignup, OwnerSignup } from '../../../auth/signup/signup.models';
import { LoginModel } from '../../../auth/login/login.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private authUrl: AuthUrl;

  constructor(private http: HttpClient) { 
    this.authUrl = new AuthUrl();
   }

  login(payload: LoginModel): Observable<any> {
    return this.http.post(this.authUrl.login, payload);
  }

  signup(payload: any): Observable<any> {
    return (payload?.user_type == "OR") ? this.signupAsOwner(payload) : this.signupAsEmployee(payload);
  }

  signupAsOwner(payload: OwnerSignup): Observable<any> {
    return this.http.post(this.authUrl.signup, payload);
  }

  signupAsEmployee(payload: EmployeeSignup): Observable<any> {
    return this.http.post(this.authUrl.signup, payload);
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(this.authUrl.forgotPassword, { email });
  }

  forgotUsername(phone: string): Observable<any> {
    return this.http.post(this.authUrl.forgotUsername, { phone });
  }
}

import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {environment} from '../environments/environment';
import {observable, Observable} from "rxjs";

declare const grecaptcha: any;

@Injectable({
  providedIn: 'root'
})
export class CheckinService {

  private readonly apiUrl: string;

  constructor(
    public httpClient: HttpClient
  ) {
    this.apiUrl = environment.apiUrl;
  }

  public createCheckin(checkin: Checkin, token: any) {
    checkin['recaptcha'] = token;
    return this.httpClient.post<Checkin>(`${this.apiUrl}/confirmation`, checkin);
  }

  public getCheckin(code: string, token: any) {
    // Post here so we can check the token
    return this.httpClient.post<Checkin>(`${this.apiUrl}/confirmation/${code}`, {'recaptcha': token});
  }

  public deleteCheckin(code: string) {
    return this.httpClient.delete<Checkin>(`${this.apiUrl}/confirmation/${code}`);
  }

  public captcha(action: string) {
    return new Observable((observable) => {
      grecaptcha.ready(() => {
        grecaptcha.execute('6LddwrsUAAAAACP2v2nRo-RFxrKc7Lg5X3s--QDU', {action: action}).then((token: any) => {
          observable.next(token);
          observable.complete();
        });
      });
    });
  }
}

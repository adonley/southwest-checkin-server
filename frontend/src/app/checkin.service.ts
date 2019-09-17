import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import { environment } from '../environments/environment';

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

  public createCheckin(checkin: Checkin) {
    return this.httpClient.post<Checkin>(`${this.apiUrl}/confirmation`, checkin);
  }

  public getCheckin(code: string) {
    return this.httpClient.get<Checkin>(`${this.apiUrl}/confirmation/${code}`);
  }

  public deleteCheckin(code: string) {
    return this.httpClient.delete<Checkin>(`${this.apiUrl}/confirmation/${code}`);
  }
}

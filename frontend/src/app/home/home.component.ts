import { Component, OnInit } from '@angular/core';
import { CheckinService } from "../checkin.service";
import {Observable} from "rxjs";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  constructor(
    public checkinService: CheckinService
  ) { }

  ngOnInit() {
  }

  public deleteCheckin() {

  }

  public getCheckin() {
    
  }

  public onSubmitCheckin() {
    this.checkinService.createCheckin().subscribe((s: Observable<Checkin>) => {

    }, (err: Error) => {

    });
  }
}

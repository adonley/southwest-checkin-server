import { Component, OnInit } from '@angular/core';
import { CheckinService } from "../checkin.service";

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

  public onSubmit() {

  }
}

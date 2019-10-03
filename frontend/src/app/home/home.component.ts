import {Component, OnInit} from '@angular/core';
import {CheckinService} from "../checkin.service";
import {FormBuilder, FormGroup, Validators} from "@angular/forms";
import {CheckinComponent} from "../checkin/checkin.component";
import {Angulartics2, EventTrack} from "angulartics2";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  public checkinSendForm: FormGroup;
  public checkinGetForm: FormGroup;

  public errorsSend: string[];
  public errorsGet: string[];

  public sendCheckinResponse: Checkin;
  public getCheckinResponse: Checkin;

  public JSON: any;

  constructor(
    public angulartics2: Angulartics2,
    public formBuilder: FormBuilder,
    public checkinService: CheckinService
  ) {
    this.JSON = JSON;
  }

  ngOnInit() {
    this.errorsGet = [];
    this.errorsSend = [];

    this.checkinSendForm = this.formBuilder.group({
      'confirmation': ['', [Validators.required, Validators.minLength(7), Validators.maxLength(7)]],
      'firstName': ['', [Validators.required, Validators.minLength(2)]],
      'lastName': ['', [Validators.required, Validators.minLength(2)]],
      'phone': ['', [Validators.minLength(10), Validators.maxLength(10)]],
      'email': ['', [Validators.email]],
    });

    this.checkinGetForm = this.formBuilder.group({
      'confirmation': ['', [Validators.required, Validators.minLength(7), Validators.maxLength(7)]]
    });

    this.sendCheckinResponse = undefined;
    this.getCheckinResponse = undefined;
  }

  public deleteCheckin() {
    this.checkinService.deleteCheckin(this.checkinGetForm.controls['confirmation'].value).subscribe((c: Checkin) => {

    }, (err: any) => {

    });
  }

  public getCheckin() {
    this.angulartics2.eventTrack.next({
      action: 'click',
      properties: {
        category: 'getReservationInfo',
        label: 'reservation',
        value: this.checkinGetForm.controls['confirmation'].value
      }
    });
    this.checkinService.getCheckin(this.checkinGetForm.controls['confirmation'].value).subscribe((c: Checkin) => {
      this.getCheckinResponse = c;
    }, (err: any) => {
      this.errorsGet = err.error.errors;
    });
  }

  public onSubmitCheckin() {
    this.angulartics2.eventTrack.next({
      action: 'click',
      properties: {
        category: 'submitReservationInfo',
        label: 'reservation',
        value: this.checkinSendForm.controls['confirmation'].value
      }
    });
    this.checkinService.createCheckin(this.checkinSendForm.value).subscribe((c: Checkin) => {
      this.sendCheckinResponse = c;
    }, (err: any) => {
      this.errorsSend = err.error.errors;
    });
  }

  public resetGetCheckinForm() {
    this.checkinGetForm.reset();
  }

  public resetNewCheckinForm() {
    this.checkinSendForm.reset();
  }
}

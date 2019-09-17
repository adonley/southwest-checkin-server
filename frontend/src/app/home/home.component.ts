import { Component, OnInit } from '@angular/core';
import { CheckinService } from "../checkin.service";
import {FormBuilder, FormGroup, Validators} from "@angular/forms";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  public checkinSendForm: FormGroup;
  public checkinGetForm: FormGroup;

  public checkin: Checkin;

  constructor(
    public formBuilder: FormBuilder,
    public checkinService: CheckinService
  ) { }

  ngOnInit() {
    this.checkinSendForm = this.formBuilder.group({
      'confirmation': ['', [Validators.required, Validators.minLength(7), Validators.maxLength(7)]],
      'firstName': ['', [Validators.required, Validators.minLength(2)]],
      'lastName': ['', [Validators.required, Validators.minLength(2)]],
      'phone': ['', [Validators.minLength(10), Validators.maxLength(10)]],
      'email': ['', [Validators.required]],
    });

    this.checkinGetForm = this.formBuilder.group({
      'confirmation': ['', [Validators.required, Validators.minLength(7), Validators.maxLength(7)]]
    });

    this.checkin = undefined;
  }

  public deleteCheckin() {
    this.checkinService.deleteCheckin(this.checkinGetForm.controls['confirmation'].value).subscribe((c: Checkin) => {

    }, (err: Error) => {

    });
  }

  public getCheckin() {
    this.checkinService.getCheckin(this.checkinGetForm.controls['confirmation'].value).subscribe((c: Checkin) => {
      this.checkin = c;
    }, (err: Error) => {

    });
  }

  public onSubmitCheckin() {
    this.checkinService.createCheckin().subscribe((c: Checkin) => {
      this.checkin = c;
    }, (err: Error) => {

    });
  }
}

import { Component, OnInit } from '@angular/core';
import { CheckinService } from "../checkin.service";
import {Observable} from "rxjs";
import {FormBuilder, FormGroup, Validators} from "@angular/forms";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  public checkinSendForm: FormGroup;
  public checkinGetForm: FormGroup;

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
  }

  public deleteCheckin() {
    this.checkinService.deleteCheckin().subscribe((c: Observable<Checkin>) => {

    }, (err: Error) => {

    });
  }

  public getCheckin() {
    this.checkinService.getCheckin().subscribe((c: Observable<Checkin>) => {

    }, (err: Error) => {

    });
  }

  public onSubmitCheckin() {
    this.checkinService.createCheckin().subscribe((c: Observable<Checkin>) => {

    }, (err: Error) => {

    });
  }
}

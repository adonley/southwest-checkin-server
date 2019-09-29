import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-checkin',
  templateUrl: './checkin.component.html',
  styleUrls: ['./checkin.component.scss']
})
export class CheckinComponent {

  @Input() checkin: Checkin;

  constructor() { }
}

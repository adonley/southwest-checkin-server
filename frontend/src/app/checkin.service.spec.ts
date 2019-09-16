import { TestBed } from '@angular/core/testing';

import { CheckinService } from './checkin.service';

describe('CheckinService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CheckinService = TestBed.get(CheckinService);
    expect(service).toBeTruthy();
  });
});

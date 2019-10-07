from unittest import TestCase, mock
from unittest.mock import MagicMock
from test_variables import past_confirmation, CHECKIN_RESPONSE
import main
import southwest


class TestMain(TestCase):
    def test_check_confirmations_with_past(self):
        main.get_close_confirmations = MagicMock(return_value=past_confirmation())
        old_main = main.checkin
        main.checkin = MagicMock(return_value=None)
        assert main.check_confirmations() is None
        main.checkin.assert_called()
        main.checkin = old_main

    @mock.patch('southwest.Reservation.checkin')
    @mock.patch('redis.Redis.set')
    def test_checkin_with_past(self, redis_set, checkin_mocked):
        confirmations = past_confirmation()
        checkin_mocked.return_value = CHECKIN_RESPONSE
        redis_set.return_value = 1
        index = 0
        for c in confirmations:
            ret = main.checkin(c, index)
            assert len(ret['flightInfo'][index]['results']) == 2
            assert ret['flightInfo'][index]['checkedIn'] is True
            assert ret['flightInfo'][index]['failed'] is False
            index += 1

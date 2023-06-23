from datetime import datetime, timedelta
import json

class Clock:

    def __init__(self) -> None:
        # create array of datetimes, starting 24 hours ago rounded to the nearest 10 minutes
        # and increasing in steps of 10 minutes up to current datetime.
        yday = self.yesterday()
        yday_rounded = yday - timedelta(minutes=yday.minute % 10,
                                        seconds=yday.second,
                                        microseconds=yday.microsecond)
        self.times = [yday_rounded + timedelta(minutes = (10 * i)) for i in range(1, 145)]


    def json_time_list(self):
        print_times = map(lambda t : t.strftime("%H:%M"), self.times)
        return json.dumps(list(print_times))


    def now(self) -> datetime:
        return datetime.now()


    def yesterday(self) -> datetime:
        return datetime.now() - timedelta(days=1)
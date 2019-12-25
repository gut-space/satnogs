import random
from orbit_predictor.predictors.base import PredictedPass
import datetime as dt

class FakePredictor():
    def __init__(self, sate_id: str, delay: int, after: int):
        self._sate_id = sate_id
        self._delay = delay
        self._after = after

    def get_next_pass(self, location, when_utc=None, max_elevation_gt=5,
                      aos_at_dg=0, limit_date=None):
        if when_utc is None:
            when_utc = dt.datetime.utcnow()
        
        delay = self._delay
        after = self._after
        return PredictedPass(location, self._sate_id, random.randint(aos_at_dg, 90),
            when_utc + dt.timedelta(seconds=after), when_utc + dt.timedelta(seconds=after + delay), delay,
            None, when_utc + dt.timedelta(seconds=after + delay / 2))

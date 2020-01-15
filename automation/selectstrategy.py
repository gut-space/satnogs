from collections import namedtuple
from typing import Dict, Iterable, List, Tuple, TypeVar
from datetimerange import DateTimeRange

from orbit_predictor.predictors import PredictedPass

T = TypeVar('T')
Observation = namedtuple("Entry", ("data", "pass_", "range"))

def aos_priority_strategy(data: Iterable[Tuple[T, PredictedPass]]) -> Iterable[Tuple[T, PredictedPass, DateTimeRange]]:
    entries: List[Observation] = []
    for obj, pass_ in data:
        range_ = DateTimeRange(pass_.aos, pass_.los)
        entry = Observation(obj, pass_, range_)
        entries.append(entry)

    entries.sort(key=lambda ent: ent.pass_.aos)

    result = []
    previous_los = None
    for entry in entries:
        if previous_los is not None and previous_los in entry.range:
            entry.range.set_start_datetime(previous_los)
            if not entry.range.is_valid_timerange():
                continue
        
        previous_los = entry.pass_.los
        result.append(entry)

    return result



    
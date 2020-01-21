from collections import namedtuple
from typing import Dict, Iterable, List, Tuple, TypeVar, Callable, Hashable

from datetimerange import DateTimeRange
from orbit_predictor.predictors import PredictedPass

T = TypeVar('T')
Observation = namedtuple("Entry", ("data", "pass_", "range"))

def _to_observations(data: Iterable[Tuple[T, PredictedPass]]) -> List[Observation]:
    entries: List[Observation] = []
    for obj, pass_ in data:
        range_ = DateTimeRange(pass_.aos, pass_.los)
        entry = Observation(obj, pass_, range_)
        entries.append(entry)
    return entries

def create_strategy(sort_key: Callable[[Observation], Hashable],
        selector: Callable[[T, PredictedPass, DateTimeRange, DateTimeRange], DateTimeRange],
        min_seconds=1):
    def strategy(data: Iterable[Tuple[T, PredictedPass]]) -> Iterable[Tuple[T, PredictedPass, DateTimeRange]]:
        entries = _to_observations(data)

        entries.sort(key=sort_key)
        
        result = []
        while len(entries) != 0:
            top = entries[0]
            result.append(top)
            entries.remove(top)
            filtered_entries = []
            for entry in entries:
                if top.range.is_intersection(entry.range):
                    left_range = DateTimeRange(entry.range.start_datetime, top.range.start_datetime)
                    right_range = DateTimeRange(top.range.end_datetime, entry.range.end_datetime)
                    if not left_range.is_valid_timerange():
                        left_range = None
                    if not right_range.is_valid_timerange():
                        right_range = None  
                    if left_range is None and right_range is None:
                        continue
                    selected_range = selector(entry.data, entry.pass_, left_range, right_range)
                    if selected_range is None:
                        continue
                
                    entry.range.set_start_datetime(selected_range.start_datetime)
                    entry.range.set_end_datetime(selected_range.end_datetime)
                    if not entry.range.is_valid_timerange():
                        raise ValueError("Daterange is invalid")
                if entry.range.get_timedelta_second() < min_seconds:
                    continue
                filtered_entries.append(entry)
            entries = filtered_entries
        return result
    return strategy

aos_priority_strategy = create_strategy(lambda o: o.pass_.aos, lambda _d, _p, _lr, rr: rr)
def max_elevation_selector(_, pass_, left_range, right_range):
    max_elevation_date = pass_.max_elevation_date
    for r in (left_range, right_range):
        if r is not None and max_elevation_date in r:
            return r
    return None
max_elevation_strategy = create_strategy(lambda o: -o.pass_.max_elevation_deg, max_elevation_selector)

def strategy_factory(name: str):
    if name == "aos":
        return aos_priority_strategy
    if name == "max-elevation":
        return max_elevation_strategy
    raise LookupError("Unknown strategy")
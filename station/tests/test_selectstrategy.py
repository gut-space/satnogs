import datetime
import unittest

from datetimerange import DateTimeRange
from orbit_predictor.predictors import PredictedPass
from orbit_predictor.locations import Location

import selectstrategy

def get_pass(location, name, aos, los, max_elevation, when_max_elevation = 0.5):
    duration_s = (los - aos).total_seconds()
    max_elevation_date = aos + datetime.timedelta(seconds=duration_s * when_max_elevation)
    return PredictedPass(location, name, max_elevation, aos, los, duration_s, max_elevation_date=max_elevation_date)

location = Location("TEST_LOC", 50, 20, 100)
start = datetime.datetime(2020, 1, 1, 0, 0, 0)
moments = {}
for i in range(10):
    moments[i] = start + datetime.timedelta(minutes=i)

class TestSelectStrategy(unittest.TestCase):
    #    | 0    1    2    3    4    5    6    7    8    9
    # 90 | |--- A ---|
    # 80 |      |- B |
    # 70 |      |-*- C --|
    # 60 |                          |--- D ---|
    # 50 |                     |--- E *--|
    # 40 |                     |-*- F ---|
    # 30 |                                    |--G |-- H |
    def setUp(self):
        A = get_pass(location, "A", moments[0], moments[2], 90)
        B = get_pass(location, "B", moments[1], moments[2], 80)
        C = get_pass(location, "C", moments[1], moments[3], 70, 0.25)
        D = get_pass(location, "D", moments[5], moments[7], 60)
        E = get_pass(location, "E", moments[4], moments[6], 50, 0.75)
        F = get_pass(location, "F", moments[4], moments[6], 40, 0.25)
        G = get_pass(location, "G", moments[7], moments[8], 30)
        H = get_pass(location, "H", moments[8], moments[9], 30)

        self.dataset = [(item.sate_id, item) for item in [A,B,C,D,E,F,G,H]]

    def test_aos_strategy(self):
        strategy = selectstrategy.aos_priority_strategy
        observations = strategy(self.dataset)

        expected = [
            ("A", DateTimeRange(moments[0], moments[2])),
            ("C", DateTimeRange(moments[2], moments[3])),
            ("E", DateTimeRange(moments[4], moments[6])),
            ("D", DateTimeRange(moments[6], moments[7])),
            ("G", DateTimeRange(moments[7], moments[8])),
            ("H", DateTimeRange(moments[8], moments[9]))
        ]

        self.assertEqual(len(observations), len(expected))
        for (result_name, _, result_range), (expected_name, exprected_range) in zip(observations, expected):
            self.assertEqual(result_name, expected_name)
            self.assertEqual(result_range, exprected_range)

    def test_max_elevation_strategy(self):
        strategy = selectstrategy.max_elevation_strategy
        observations = strategy(self.dataset)

        expected = [
            ("A", DateTimeRange(moments[0], moments[2])),
            ("D", DateTimeRange(moments[5], moments[7])),
            ("F", DateTimeRange(moments[4], moments[5])),
            ("G", DateTimeRange(moments[7], moments[8])),
            ("H", DateTimeRange(moments[8], moments[9]))
        ]

        self.assertEqual(len(observations), len(expected))
        for (result_name, _, result_range), (expected_name, exprected_range) in zip(observations, expected):
            self.assertEqual(result_name, expected_name)
        self.assertEqual(result_range, exprected_range)
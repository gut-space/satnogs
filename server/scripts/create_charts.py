#!/usr/bin/env python3

# This script generates fly-over charts for observations that have TLE
# information recorded.

from typing import Dict
from app.controllers.receive import make_charts
from app.repository import Repository, Station, StationId

if __name__ == '__main__':
    stations: Dict[StationId, Station] = { }

    repository = Repository()
    observation_count = repository.count_observations()

    STEP = 100
    limit = STEP
    offset = 0
    index = 0

    while limit < observation_count:
        # ToDo: Add filtration when MR with filtration will be merged.
        observations = repository.read_observations(limit=limit, offset=offset)

        for observation in observations:
            if observation.tle is None:
                continue
            station_id = observation["station_id"]
            if station_id in stations:
                station = stations[station_id]
            else:
                station = repository.read_station(station_id)
                stations[station_id] = station

            make_charts(observation, station)
            index += 1
            print("Processed %s/%s observation" % (index, observation_count))

        offset = limit
        limit += STEP

    print("Finish!")

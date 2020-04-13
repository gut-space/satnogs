# This script generates fly-over charts for observations that have TLE
# information recorded.

from typing import Dict
from app.controllers.receive import make_charts
from app.repository import Repository, Station, StationId

if __name__ == '__main__':
    stations: Dict[StationId, Station] = { }

    repository = Repository()
    observation_count = repository.count_observations()

    print("There are a total of %d observations" % observation_count)

    STEP = 100
    limit = STEP
    offset = 0
    index = 0

    while offset < observation_count:
        # ToDo: Add filtration when MR with filtration will be merged.
        observations = repository.read_observations(limit=limit, offset=offset)

        print("Processing batch of %d observations" % len(observations))

        for observation in observations:
            if observation['tle'] is None:
                print("No TLE info for observation %d, skipping." % observation['obs_id'])
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

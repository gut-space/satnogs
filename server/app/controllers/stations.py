from app.repository import Repository
from flask import render_template
from app import app, utils

from app.pagination import Pagination, use_pagination

@app.route('/stations')
@use_pagination()
def stations(limit_and_offset):
    '''This function retrieves list of all registered ground stations.'''
    repository = Repository()
    stations = repository.read_stations(**limit_and_offset)
    statistics = repository.read_stations_statistics(**limit_and_offset)
    station_count = repository.count_stations()
    # Now convert the data to a list of objects that we can pass to the template.
    stationlist = []

    for station, stat in zip(stations, statistics):
        x = {}
        x['station_id'] = station['station_id']
        x['name'] = station['name']
        x['coords'] = utils.coords(station['lon'], station['lat'])
        x['descr'] = station['descr']
        x['config'] = station['config']
        x['registered'] = station['registered']
        x['lastobs'] = stat["last_los"]
        x['cnt'] = stat["observation_count"]

        stationlist.append(x)

    return 'stations.html', dict(stations=stationlist, item_count=station_count)



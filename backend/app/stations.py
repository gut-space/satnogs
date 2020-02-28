from app.repository import Repository
from flask import render_template
from app import app, utils

@app.route('/stations')
def stations():
    '''This function retrieves list of all registered ground stations.'''

    repository = Repository()
    data = repository.read_stations()

    # Now convert the data to a list of objects that we can pass to the template.
    stationlist = []

    for station, count, lastobs in data:
        x = {}
        x['station_id'] = station['station_id']
        x['name'] = station['name']
        x['coords'] = utils.coords(station['lon'], station['lat'])
        x['descr'] = station['descr']
        x['config'] = station['config']
        x['registered'] = station['registered']
        x['lastobs'] = lastobs
        x['cnt'] = count

        stationlist.append(x)

    # Generate some basic stats.
    stats = "Showing %d ground station(s)." % len(data)

    return render_template('stations.html', stations=stationlist, stats=stats)



from app.repository import Repository
from flask import render_template, abort
from app import app, utils

@app.route('/station/<station_id>')
def station(station_id = None):

    repository = Repository()
    item = repository.read_station(station_id)
    if item is None:
        abort(404, "Station not found")

    station, count, lastobs = item
    photos = repository.read_station_photos(station_id)

    x = {}
    files = []

    x = {}
    x['station_id'] = station['station_id']
    x['name'] = station['name']
    x['coords'] = utils.coords(station['lon'], station['lat'])
    x['descr'] = station['descr']
    x['config'] = station['config']
    x['registered'] = station['registered']
    x['lastobs'] = lastobs
    x['cnt'] = count

    for photo in photos:
        y = {}
        y['filename'] = photo['filename']
        y['descr'] = photo['descr']
        y['sort'] = photo['sort']
        files.append(y)

    return render_template('station.html', station = x, files = files)

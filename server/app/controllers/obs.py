from flask import abort, Response

from app import app, tle_diagrams, cache
from app.repository import ObservationId, Repository
from app.pagination import use_pagination

@app.route('/obs/<obs_id>')
@use_pagination(5)
def obs(obs_id: ObservationId = None, limit_and_offset = None):
    if obs_id is None:
        abort(300, description="ID is required")

    repository = Repository()
    with repository.transaction():
        observation = repository.read_observation(obs_id)

        if observation is None:
            abort(404, "Observation not found")
    
        files = repository.read_observation_files(observation["obs_id"],
            **limit_and_offset)
        files_count = repository.count_observation_files(obs_id)
        satellite = repository.read_satellite(observation["sat_id"])

    return 'obs.html', dict(obs = observation, files=files,
        sat_name=satellite["sat_name"], item_count=files_count)

def _tle_plot(obs_id: ObservationId, plot_func):
    repository = Repository()
    observation = repository.read_observation(obs_id)
    
    if observation is None:
        abort(404, "Observation not found")
    if observation["tle"] is None:
        abort(404, "TLE not found")

    station = repository.read_station(observation["station_id"])[0]
    location = tle_diagrams.Location(station["lat"], station["lon"], 0)
    stream = plot_func(location,
        observation["tle"], observation["aos"], observation["los"])
    return Response(stream.getvalue(), mimetype='image/png')

@app.route('/obs/<obs_id>/az_el_polar.png')
@cache.cached()
def obs_polar_plot(obs_id: ObservationId):
    return _tle_plot(obs_id, tle_diagrams.generate_polar_plot_png)

@app.route('/obs/<obs_id>/az_el_by_time.png')
@cache.cached()
def obs_by_time_plot(obs_id: ObservationId):
    return _tle_plot(obs_id, tle_diagrams.generate_by_time_plot_png)
from flask import abort

from app import app
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

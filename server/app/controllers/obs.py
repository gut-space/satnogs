from flask import render_template, abort
from app import app
from app.repository import Repository

@app.route('/obs/<obs_id>')
def obs(obs_id = None):
    if obs_id is None:
        abort(300, description="ID is required")

    repository = Repository()
    with repository.transaction():
        observation = repository.read_observation(obs_id)

        if observation is None:
            abort(404, "Observation not found")
    
        files = repository.read_observation_files(observation["obs_id"])
        satellite = repository.read_satellite(observation["sat_id"])

    return render_template('obs.html', obs = observation, files=files, sat_name=satellite["sat_name"])

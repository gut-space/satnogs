from flask import render_template, abort
from . import app
from app.repository import Repository
import psycopg2

@app.route('/obs/<obs_id>')
def obs(obs_id = None):
    if obs_id is None:
        abort(300, description="ID is required")

    repository = Repository()
    observation = repository.read_observation(obs_id)

    if observation is None:
        abort(404, "Observation not found")

    return render_template('obs.html', obs = observation)

from flask import render_template
from app import app

@app.route('/obs/<obs_id>')
def obs(obs_id = None):
    return render_template('obs.html', obs_id = obs_id)

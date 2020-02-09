from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/obs/<obs_id>')
def obs(obs_id = None):
    return render_template('obs.html', obs_id = obs_id)

@app.route('/obslist/')
def obslist():
    return render_template('obslist.html')
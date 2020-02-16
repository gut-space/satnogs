from flask import render_template, send_from_directory, send_file
from app import app
from app import obslist
from app import obs
from app import stations

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/favicon.png')
def favicon():
    return send_file('favicon.png')

@app.route('/data/<path:path>')
def send_js(path):
    return send_from_directory('data', path)
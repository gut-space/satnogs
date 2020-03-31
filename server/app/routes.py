from flask import render_template, send_from_directory, send_file
from app import app
# Load routes from modules in "controllers" directory
from app.controllers import *
from app.utils import get_footer

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", footer = get_footer())

@app.route('/favicon.png')
def favicon():
    return send_file('favicon.png')

@app.route('/data/<path:path>')
def send_js(path):
    return send_from_directory('data', path)
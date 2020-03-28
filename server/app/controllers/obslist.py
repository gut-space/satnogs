from flask import render_template
import sys

from app import app
from app.repository import Repository

@app.route('/obslist')
def obslist():
    '''This function retrieves observations list from a local database and displays it.'''
    repository = Repository()
    obslist = repository.read_observations()
    satellites_list = repository.read_satellites()
    satellites_dict = { sat["sat_id"]: sat["sat_name"] for sat in satellites_list }
    for obs in obslist:
        obs["sat_name"] = satellites_dict[obs["sat_id"]]

    return render_template('obslist.html', obslist=obslist)
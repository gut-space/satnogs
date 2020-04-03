from flask import render_template

from app import app
from app.repository import Repository
from app.pagination import Pagination, use_pagination

@app.route('/obslist')
@use_pagination()
def obslist(limit_and_offset):
    '''This function retrieves observations list from a local database and displays it.'''
    repository = Repository()
    obslist = repository.read_observations(**limit_and_offset)
    satellites_list = repository.read_satellites()
    observation_count = repository.count_observations()
    satellites_dict = { sat["sat_id"]: sat["sat_name"] for sat in satellites_list }
    for obs in obslist:
        obs["sat_name"] = satellites_dict[obs["sat_id"]]

    return 'obslist.html', dict(obslist=obslist, item_count=observation_count)
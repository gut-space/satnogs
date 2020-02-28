from flask import render_template
import sys

from app import app
from app.repository import Repository

@app.route('/obslist')
def obslist():
    '''This function retrieves observations list from a local database and displays it.'''
    repository = Repository()
    obslist = repository.read_observations()
    
    # Generate some basic stats.
    stats = "Showing the last %d observations." % len(obslist)

    return render_template('obslist.html', obslist=obslist, stats=stats)
from flask import render_template
from app import app
import sys
import psycopg2

@app.route('/obslist')
def obslist():
    '''This function retrieves observations list from a local database and displays it.'''

    try:

        # Open a connection
        # TODO: move this to a config file and read it in one common function
        conn = psycopg2.connect(host="localhost", database="satnogs", user="satnogs", password="")

        # Send query
        q = "SELECT obs_id, aos, tca, los, sat_name, filename FROM observations ORDER by aos desc LIMIT 100"
        cursor = conn.cursor()
        cursor.execute(q)

        # Fetch the data
        data = cursor.fetchall()
        cursor.close()
        conn.close()

    except Exception as e:
        return "Unable to connect to Postgres DB: %s " % e

    # Now convert the data to a list of objects that we can pass to the template.
    obslist = []

    for row in data:
        x = {}
        x['obs_id'] = row[0]
        x['aos'] = row[1]
        x['tca'] = row[2]
        x['los'] = row[3]
        x['sat_name'] = row[4]
        x['filename'] = row[5]
        x['thumbfile'] = "thumb-" + row[5]

        obslist.append(x)

    # Generate some basic stats.
    stats = "Showing the last %d observations." % len(data)

    return render_template('obslist.html', obslist=obslist, stats=stats)
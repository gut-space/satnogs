from flask import render_template
from . import app
import psycopg2

@app.route('/obs/<obs_id>')
def obs(obs_id = None):

    try:

        cfg = app.config["database"]

        # Open a connection
        conn = psycopg2.connect(**cfg)

        # Send query
        q = "SELECT obs_id, aos, tca, los, sat_name, filename FROM observations WHERE obs_id = " + obs_id;
        cursor = conn.cursor()
        cursor.execute(q)

        # Fetch the data
        data = cursor.fetchall()
        cursor.close()
        conn.close()

    except Exception as e:
        return "Error when connecting to DB: %s" % e

    row = data[0]
    x = {}
    x['obs_id'] = row[0]
    x['aos'] = row[1]
    x['tca'] = row[2]
    x['los'] = row[3]
    x['sat_name'] = row[4]
    x['filename'] = row[5]
    x['thumbfile'] = "thumb-" + row[5]

    return render_template('obs.html', obs = x)

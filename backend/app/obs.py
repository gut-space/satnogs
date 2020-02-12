from flask import render_template
from app import app
import psycopg2

@app.route('/obs/<obs_id>')
def obs(obs_id = None):

    try:

        # Open a connection
        # TODO: move this to a config file and read it in one common function
        conn = psycopg2.connect(host="localhost", database="satnogs", user="satnogs")

        # Send query
        q = "SELECT obs_id, aos, tca, los, sat_name, filename FROM observations WHERE obs_id = " + obs_id;
        cursor = conn.cursor()
        cursor.execute(q)

        # Fetch the data
        data = cursor.fetchall()
        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        return "Unable to connect to Postgres DB: %s " % e

    row = data[0]
    x = {}
    x['obs_id'] = row[0]
    x['aos'] = row[1]
    x['tca'] = row[2]
    x['los'] = row[3]
    x['sat_name'] = row[4]
    x['filename'] = row[5]

    return render_template('obs.html', obs = x)

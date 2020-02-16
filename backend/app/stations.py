from flask import render_template
from app import app, conf, utils
import sys
import psycopg2

@app.route('/stations')
def stations():
    '''This function retrieves list of all registered ground stations.'''

    try:
        cfg = conf.getConfig()

        # Open a connection
        conn = psycopg2.connect(host= cfg.db_host, database=cfg.db_name, user=cfg.db_user, password=cfg.db_pass)

        # Send query
        q = """ SELECT t.station_id, t.name, t.lon, t.lat, t.descr, t.config, t.registered, t.lastobs, x.cnt
                FROM stations t,
                (select station_id, count(*) as cnt FROM observations GROUP BY station_id) x
                where t.station_id = x.station_id
                ORDER by cnt"""
        cursor = conn.cursor()
        cursor.execute(q)

        # Fetch the data
        data = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        return "Unable to connect to Postgres DB: %s " % e

    # Now convert the data to a list of objects that we can pass to the template.
    stationlist = []

    for row in data:
        x = {}
        x['station_id'] = row[0]
        x['name'] = row[1]
        x['coords'] = utils.coords(row[2], row[3])
        x['descr'] = row[4]
        x['config'] = row[5]
        x['registered'] = row[6]
        x['lastobs'] = row[7]
        x['cnt'] = row[8]

        stationlist.append(x)

    # Generate some basic stats.
    stats = "Showing %d ground station(s)." % len(data)

    return render_template('stations.html', stations=stationlist, stats=stats)



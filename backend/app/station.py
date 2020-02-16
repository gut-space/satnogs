from flask import render_template
from app import app, conf, utils
import psycopg2

@app.route('/station/<station_id>')
def station(station_id = None):

    try:

        cfg = conf.getConfig()

        # Open a connection
        conn = psycopg2.connect(host= cfg.db_host, database=cfg.db_name, user=cfg.db_user, password=cfg.db_pass)

        # Send query
        q = """ SELECT t.station_id, t.name, t.lon, t.lat, t.descr, t.config, t.registered, t.lastobs, x.cnt
                FROM stations t
                LEFT JOIN
                (select station_id, count(*) as cnt FROM observations WHERE station_id = """ + station_id + """
                GROUP BY station_id) x
                ON t.station_id = x.station_id WHERE t.station_id = """ + station_id + """
                """
        cursor = conn.cursor()
        cursor.execute(q)

        # Fetch the data
        data = cursor.fetchall()

        q2 = "SELECT filename, descr, sort FROM station_photos WHERE station_id=" + station_id
        cursor.execute(q2)
        data2 = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as e:
        return "Error when connecting to DB: %s" % e

    x = {}
    files = []

    for row in data:
        x['station_id'] = row[0]
        x['name'] = row[1]
        x['coords'] = utils.coords(row[2], row[3])
        x['descr'] = row[4]
        x['config'] = row[5]
        x['registered'] = row[6]
        x['lastobs'] = row[7]
        x['cnt'] = row[8]

    for row in data2:
        y = {}
        y['filename'] = row[0]
        y['descr'] = row[1]
        y['sort'] = row[2]
        files.append(y)

    return render_template('station.html', station = x, files = files)

import datetime
import os.path
import uuid

from flask import request, abort
import psycopg2
from webargs import fields
from webargs.flaskparser import use_args

from . import app
from .authorize_station import authorize_station
from .utils import make_thumbnail

cfg = app.config["database"]

@app.route('/receive', methods=["POST",])
@authorize_station
@use_args({
    'file': fields.Field(validate=lambda file: file.mimetype == "image/png", location="files"),
    'aos': fields.DateTime(required=True),
    'tca': fields.DateTime(required=True),
    'los': fields.DateTime(required=True),
    'sat': fields.Str(required=True),
    'notes': fields.Str(required=False)
})
def receive(station_id, args):
    if len(request.files) == 0:
        abort(400, description="Missing file")

    file_ = args['file']
    filename = "%s-%s" % (str(uuid.uuid4()), file_.filename)

    with psycopg2.connect(**cfg) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT sat_id FROM satellites WHERE sat_name = %s LIMIT 1;", (args["sat"],))
            row = cursor.fetchone()
            if row is None:
                abort(400, description="Unknown satellite")
            sat_id = row[0]
            cursor.execute(
                "INSERT INTO observations (aos, tca, los, sat_id, sat_name, filename, notes, station_id)"
                "VALUES (%(aos)s, %(tca)s, %(los)s, %(sat_id)s, %(sat_name)s, %(filename)s, %(notes)s, %(station_id)s);",
                {
                    'aos': args['aos'].isoformat(),
                    'tca': args['tca'].isoformat(),
                    'los': args['los'].isoformat(),
                    'sat_id': sat_id,
                    'sat_name': args['sat'],
                    'filename': filename,
                    'notes': args.get('notes'),
                    'station_id': int(station_id)
                }
            )
            conn.commit()

    root = app.config["storage"]['image_root']
    path = os.path.join(root, filename)
    file_.save(path)
    thumb_path = os.path.join(root, "thumbs", "thumb-" + filename)
    make_thumbnail(path, thumb_path)
    return '', 204
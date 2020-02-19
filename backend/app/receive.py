import datetime
import hashlib
import hmac
import os.path
import uuid

from flask import request, abort
import psycopg2

from . import app

SIG_LIFETIME = datetime.timedelta(minutes=2, seconds=30)
AUTHORIZATION_ALGORITHM = "HMAC-SHA256"

cfg = app.config["database"]

def verify(sig: str, secret: bytes, body: str, timestamp: str):
    sig_basestring = ("%s:%s" % (timestamp, body)).encode()
    computed_sha = hmac.new(secret, sig_basestring, digestmod=hashlib.sha256).hexdigest()
    return sig == computed_sha

def get_normalized_body_string():
    file_hashes = { k: hashlib.sha1(v.read()).hexdigest() for k, v in request.files.items() }
    body = {}
    body.update(request.form)
    body.update(file_hashes)
    pairs = sorted(body.items(), key=lambda p: p[0])
    return "&".join("%s=%s" % (k, v) for k, v in pairs)

def get_secret(conn, station_id):
    with conn.cursor() as c:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        c.execute(query, (station_id,))
        row = c.fetchone()
        if row is None:
            return None
        return row[0].tobytes()

def verify_request(conn):
    header = request.headers.get("Authorization")
    if header is None:
        return False, None
    algorithm, content = header.split()
    if algorithm != AUTHORIZATION_ALGORITHM:
        return False, None
    station_id, timestamp, sig = content.split(",")
    
    timestamp_date = datetime.datetime.fromisoformat(timestamp)
    now = datetime.datetime.utcnow()
    delta = abs(now - timestamp_date)
    if delta > SIG_LIFETIME:
        return False, None

    secret = get_secret(conn, station_id)
    body = get_normalized_body_string()
    
    return verify(sig, secret, body, timestamp), station_id

@app.route('/receive', methods=["POST",])
def receive():
    with psycopg2.connect(**cfg) as conn:
        verification_result, station_id = verify_request(conn)
        if not verification_result:
            abort(403)
        
        if len(request.files) == 0:
            abort(400)

        for f in request.files.values():
            file_ = f
            break
        file_.seek(0)

        filename = "%s-%s" % (str(uuid.uuid4()), file_.filename)
        root = app.config["storage"]['image_root']
        path = os.path.join(root, filename)
        file_.save(path)
        return '', 204
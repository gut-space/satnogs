import datetime
import hashlib

from functools import wraps

from flask import abort, request
import psycopg2

from . import app
from .hmac_token import parse_token, validate_token

AUTHORIZATION_ALGORITHM = "HMAC-SHA256"

cfg = app.config["database"]

def _get_body(request):
    file_hashes = {}
    for k, v in request.files.items():
        hash_ = hashlib.sha1(v.read()).hexdigest()
        file_hashes[k]: hash_
        v.seek(0)

    body = {}
    body.update(request.form)
    body.update(file_hashes)
    return body

def _get_secret(conn, station_id):
    with conn.cursor() as c:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        c.execute(query, (station_id,))
        row = c.fetchone()
        if row is None:
            return None
        return row[0].tobytes()

def _verify_request():
    header = request.headers.get("Authorization")
    if header is None:
        return False, None
    algorithm, token = header.split()
    if algorithm != AUTHORIZATION_ALGORITHM:
        return False, None
    
    station_id, *_ = parse_token(token)
    with psycopg2.connect(**cfg) as conn:
        secret = _get_secret(conn, station_id)
    body = _get_body(request)

    return validate_token(token, secret, body)

def authorize_station(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        res, id_ = _verify_request()
        if not res and not app.config["security"].get("ignore_hmac_validation_errors"):
            abort(401)
        return f(id_, *args, **kws)            
    return decorated_function
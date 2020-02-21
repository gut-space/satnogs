import datetime
import hashlib

from functools import wraps

from flask import abort, request
import psycopg2

from . import app
from .hmac_token import parse_token, validate_token, AUTHORIZATION_ALGORITHM

cfg = app.config["database"]

def _get_body(request):
    '''
    Return dict with request arguments..
    '''
    body = {}
    body.update(request.form)
    body.update(request.files)
    return body

def _get_secret(conn, station_id):
    '''
    Fetch station secret from database

    ToDo: Returned value should be cached to avoid DDoS and
          DB call before authorization
    '''
    with conn.cursor() as c:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        c.execute(query, (station_id,))
        row = c.fetchone()
        if row is None:
            return None
        return row[0].tobytes()

def _verify_request():
    '''Verify Authorization header in current request'''
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
    '''
    Security decorator for authorize ground station
    using HMAC signature.

    Returns
    =======
    Station id is passed as argument to your action.
    If authorization failed then request is abort with HTTP 401.

    Notes
    =====

    Authorization data must be included as "Authorize" HTTP header
    with value in format:
        HMAC-SHA256 [id],[timestamp],[sig]
    where:
        [id] - station id, corespoding to value in DB
        [timestamp] - timestamp in ISO 8601 format with second
                      precision in UTC time zone. For example:
                      "2020-02-20T18:59:59" (without quotes)
                      Timestamp may be max 2.5 minute older or newer
                      then now. It means that max token lifetime
                      is 5 minutes.
        [sig] - HMAC signature in hex format. See details below.
    Example:
        Authorization: HMAC-SHA256 1,2020-02-21T20:36:57,b9b64a880293cd6007c0f69a06cea6efd463782eb86ddb47f2686aa9294ff4ec

    Signature is created using HMAC algorithm with secred shared
    with content server on station id, timestamp and request body.
    First you need create a correct body.
        1. Get all your parameters (form data) as key-value pairs.
           Key and value should be treat as strings.
           If you attach any file then as value use SHA-1 hash
           from content (digest, hex format).
        2. Sort your pairs alphabetically
        3. Concat key and value using equal sign as hyphen
           For example if your key is named "foo" and value is "bar"
           then your pair representation is "foo=bar"
        4. Join all pair representation using "&" as delimiter
           For example: For pairs: ('foo', '1'), ('bar', '2'), ('baz', '3')
           you should use: "bar=2&baz=3&foo=1"
    Now you can create basestring for signature:
        5. Save your timestamp in ISO 8601 format with second precision.
           It must be the same timestamp as you used in header-level
        6. Concat station id, timestamp and basestring using colons
           For example for id equals "1", create date 2020-02-20 18:59:59 UTC,
           and body { 'foo': 1, 'bar': 2 } you should get:
             1:2020-02-20T18:59:59:bar=2&foo=1
    Next you should create signature:   
        7. Use HMAC algorithm with your secret on basestring

    Secret must be at least 16 cryptographic-safe random bytes.

    Example
    =======
    @app.route('/api')
    @authorize_station
    def api(station_id: str):
        pass
    '''
    @wraps(f)
    def decorated_function(*args, **kws):
        res, id_ = _verify_request()
        if not res and not app.config["security"].get("ignore_hmac_validation_errors"):
            abort(401, description="Authorization failed")
        return f(id_, *args, **kws)            
    return decorated_function
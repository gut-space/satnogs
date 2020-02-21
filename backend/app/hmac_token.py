import datetime
import hashlib
import hmac
from typing import Dict

'''
HMAC based token processing - creation, parsing and verification.
This package is designed for use in server and station side.
It should have only standard library dependencies.
'''

AUTHORIZATION_ALGORITHM = "HMAC-SHA256"
SIG_LIFETIME = datetime.timedelta(minutes=2, seconds=30)

def _handle_files_in_body(body: Dict):
    '''Replace file-like values with hashes'''
    res = {}
    for k, v in body.items():
        if hasattr(v, "read") and hasattr(v, "seek"):
            hash_ = hashlib.sha1(v.read()).hexdigest()
            res[k] = hash_
            v.seek(0)
        else:
            res[k] = v
    return res

def _get_sig_basestring(id_: str, body: Dict, date: datetime.datetime):
    '''Create basestring for signature'''
    timestamp = date.isoformat(timespec='seconds')
    body = _handle_files_in_body(body)

    pairs = sorted(body.items(), key=lambda p: p[0])
    body_string = "&".join("%s=%s" % (k, v) for k, v in pairs)
    sig_basestring = ("%s:%s:%s" % (id_, timestamp, body_string)).encode()
    return sig_basestring

def _get_signature(secret: bytes, id_: str,  body: Dict, date: datetime.datetime):
    '''Create HMAC signature using provided parameters.'''
    sig_basestring = _get_sig_basestring(id_, body, date)
    return hmac.new(secret, sig_basestring, digestmod=hashlib.sha256).hexdigest()

def _verify_signature(sig: str, secret: bytes, id_: str, body: Dict, create_date: datetime.datetime):
    '''
    Check if passed signature was created using provided parameters.
    It doesn't check if timestamp lifetime expired.
    '''
    computed_sig = _get_signature(secret, id_, body, create_date)
    return sig == computed_sig

def get_token(id_: str, secret: bytes, body: Dict, date: datetime.datetime):
    '''Create HMAC based token using provided parameters.'''
    sig = _get_signature(secret, id_, body, date)
    token = ",".join((id_, date.isoformat(timespec='seconds'), sig))
    return token

def parse_token(token: str):
    '''Split token to id, timestamp and signature'''
    id_, timestamp, sig = token.split(",")
    create_date = datetime.datetime.fromisoformat(timestamp)
    return id_, create_date, sig

def validate_token(token: str, secret: bytes, body: Dict, check_date=None):
    '''
    Check if passed token was created using provided arguments

    Parameters
    ==========
    token: str
        HMAC based token, created from id, timestamp in ISO 8601 with second precision
        and HMAC signature delimited by comma
    secret: bytes
        Crypto-safe bytes used by HMAC algorithm
    body: Dict
        Dictionary with key-value pairs which are signed by HMAC signature in token
        Key and values should be strings (or at lease primitive types) or file-like
    check_date: datetime.datetime
        The moment when token should be valid. If None is passed then now is used.

    Returns
    =======
    Pair with validation result and id_ - (bool, str).
    Validation result is True if token verify successfully or False if not.
    Id is returned even if validation fail, but you shouldn't trust that it is valid.

    Notes
    =====
    Timestamp may be max 2.5 minute older or newer
    then now. It means that max token lifetime is 5 minutes.

    Examples
    ========
    secret = b'\x9a\x19=\xfc\xd8\xe6\x13V4tD%\xf1\xfe\x1c\xdd'
    body = { 'foo': 4, 'bar':2 }
    token = '1,2020-02-21T21:09:45,2a6b59a8971f6c98bafa73abbfc8bc2809f31d205a3b081f8bc1b55a9970e778'
    res, id_ = validate_token(token, secret, body)
    if res:
        print("Authorized with %s id" % (id_,))
    else:
        print("Unauthorized")
    '''
    id_, create_date, sig = parse_token(token)

    if check_date is None:
        check_date = datetime.datetime.utcnow()
    delta = abs(check_date - create_date)
    if delta > SIG_LIFETIME:
        return False, id_

    if _verify_signature(sig, secret, id_, body, create_date):
        return True, id_
    else:
        return False, id_

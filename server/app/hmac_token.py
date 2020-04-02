import datetime
from dateutil.parser import isoparse
import hashlib
import hmac
from typing import Dict, Union, Optional

'''
HMAC based token processing - creation, parsing and verification.
This package is designed for use in server and station side.
It should have only standard library dependencies.
'''

AUTHORIZATION_ALGORITHM = "HMAC-SHA256"
SIG_LIFETIME = datetime.timedelta(minutes=2, seconds=30)

def _is_file_like(obj) -> bool:
    '''Return True if @obj is file-like. Otherwise False'''
    return hasattr(obj, "read") and hasattr(obj, "seek")

def _hash_file(obj):
    '''Return file-like hash'''
    hash_ = hashlib.sha1(obj.read()).hexdigest()
    obj.seek(0)
    return hash_

def _serialize_single_item(key, value):
    '''Serialize key-value pair for non-array value'''
    if _is_file_like(value):
        value = _hash_file(value)
    return "%s=%s" % (key, value)

def _serialize_iterable_item(key, values):
    '''Serialize key-value pair for array value'''
    return "&".join(_serialize_single_item(key, v) for v in values)

def _serialize_body(body: Dict) -> str:
    '''Serialize dictionary to string'''
    serialized_items = []
    for key, value in sorted(body.items(), key=lambda p: p[0]):
        if isinstance(value, (list, tuple)):
            serialized_item = _serialize_iterable_item(key, value)
        else:
            serialized_item = _serialize_single_item(key, value)
        serialized_items.append(serialized_item)
    return "&".join(serialized_items)

def _get_sig_basestring(id_: str, body: Dict, date: datetime.datetime):
    '''Create basestring for signature'''
    timestamp = date.isoformat(timespec='seconds')

    body_string = _serialize_body(body)
    sig_basestring = ("%s:%s:%s" % (id_, timestamp, body_string)).encode()
    return sig_basestring

def _get_signature(secret: Union[bytes, bytearray], id_: str,  body: Dict, date: datetime.datetime):
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

def get_token(id_: str, secret: Union[bytes, bytearray], body: Dict, date: datetime.datetime):
    '''Create HMAC based token using provided parameters.'''
    sig = _get_signature(secret, id_, body, date)
    token = ",".join((id_, date.isoformat(timespec='seconds'), sig))
    return token

def get_authorization_header_value(id_: str, secret: Union[bytes, bytearray], body: Dict, date: Optional[datetime.datetime]=None):
    '''
    Shorthand function for create Authorization header value

    Parameters
    ==========
    id_: str
        Station ID
    secret: bytes or bytearray
        Secret of station
    body: dict
        Body of request. Values should be:
        - strings
        - file-like objects
        - list of strings or file-like objects
    date: datetime.datetime
        Datetime in UTC (may be naive). Date when token should be valid. Default: now.

    Returns
    =======
    Valid Authorization HTTP header value.
    '''
    if date is None:
        date = datetime.datetime.utcnow()
    token = get_token(id_, secret, body, date)
    return "%s %s" % (AUTHORIZATION_ALGORITHM, token)

def parse_token(token: str):
    '''Split token to id, timestamp and signature'''
    id_, timestamp, sig = token.split(",")
    create_date = isoparse(timestamp)
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
    Validation result is None if token verify successfully or string with error message otherwise.
    Id is returned even if validation fails, but you shouldn't trust that it is valid.

    Notes
    =====
    Timestamp may be max 2.5 minutes older or newer
    then now. It means that max token lifetime is 5 minutes.

    Examples
    ========
    secret = b'\x9a\x19=\xfc\xd8\xe6\x13V4tD%\xf1\xfe\x1c\xdd'
    body = { 'foo': 4, 'bar':2 }
    token = '1,2020-02-21T21:09:45,2a6b59a8971f6c98bafa73abbfc8bc2809f31d205a3b081f8bc1b55a9970e778'
    error, id_ = validate_token(token, secret, body)
    if error is None:
        print("Authorized with %s id" % (id_,))
    else:
        print("Unauthorized: %s" % (error,))
    '''
    id_, create_date, sig = parse_token(token)

    if check_date is None:
        check_date = datetime.datetime.utcnow()
    delta = abs(check_date - create_date)
    if delta > SIG_LIFETIME:
        return "Token expired", id_

    if _verify_signature(sig, secret, id_, body, create_date):
        return None, id_
    else:
        return "Invalid signature", id_

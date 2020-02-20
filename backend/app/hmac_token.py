import datetime
import hashlib
import hmac
from typing import Dict

SIG_LIFETIME = datetime.timedelta(minutes=2, seconds=30)

def _get_sig_basestring(body: Dict, date: datetime.datetime):
    timestamp = date.isoformat(timespec='seconds')

    pairs = sorted(body.items(), key=lambda p: p[0])
    body_string = "&".join("%s=%s" % (k, v) for k, v in pairs)
    sig_basestring = ("%s:%s" % (timestamp, body_string)).encode()
    return sig_basestring

def _get_signature(secret: bytes, body: Dict, date: datetime.datetime):
    sig_basestring = _get_sig_basestring(body, date)
    return hmac.new(secret, sig_basestring, digestmod=hashlib.sha256).hexdigest()

def _verify_signature(sig: str, secret: bytes, body: Dict, create_date: datetime.datetime):
    computed_sig = _get_signature(secret, body, create_date)
    return sig == computed_sig

def get_token(id_: str, secret: bytes, body: Dict, date: datetime.datetime):
    sig = _get_signature(secret, body, date)
    token = ",".join((id_, date.isoformat(timespec='seconds'), sig))
    return token

def parse_token(token: str):
    id_, timestamp, sig = token.split(",")
    create_date = datetime.datetime.fromisoformat(timestamp)
    return id_, create_date, sig

def validate_token(token: str, secret: bytes, body: Dict, check_date=None):
    id_, create_date, sig = parse_token(token)

    if check_date is None:
        check_date = datetime.datetime.utcnow()
    delta = abs(check_date - create_date)
    if delta > SIG_LIFETIME:
        return False, id_

    if _verify_signature(sig, secret, body, create_date):
        return True, id_
    else:
        return False, id_
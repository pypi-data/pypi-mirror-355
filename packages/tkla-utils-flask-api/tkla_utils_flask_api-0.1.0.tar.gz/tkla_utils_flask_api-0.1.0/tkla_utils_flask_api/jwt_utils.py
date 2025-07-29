import jwt
from datetime import datetime, timedelta, timezone


def generate_jwt(payload, secret, exp_minutes=60):
    payload['exp'] = datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)
    return jwt.encode(payload, secret, algorithm='HS256')

def decode_jwt(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


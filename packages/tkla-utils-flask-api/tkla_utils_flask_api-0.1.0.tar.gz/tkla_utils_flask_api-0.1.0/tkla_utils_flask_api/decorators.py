from functools import wraps
from flask import request
from .jwt_utils import decode_jwt
from .responses import error_response

def require_jwt(secret, roles=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            decoded = decode_jwt(token, secret)
            if not decoded:
                return error_response("Token inválido o expirado", 401)
            if roles and decoded.get('role') not in roles:
                return error_response("No autorizado", 403)
            return f(*args, **kwargs, user=decoded)
        return wrapper
    return decorator

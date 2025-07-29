import uuid
import secrets

def generate_random_token(length=32):
    return secrets.token_hex(length // 2)

def generate_uuid_token():
    return str(uuid.uuid4())

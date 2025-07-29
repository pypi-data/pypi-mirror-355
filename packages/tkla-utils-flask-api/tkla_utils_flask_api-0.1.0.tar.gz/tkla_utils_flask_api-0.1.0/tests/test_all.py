# tests/test_all.py
import unittest
from tkla_utils_flask_api import jwt_utils, hashing, tokens, time_utils, responses

class TestTklaUtilsFlaskAPI(unittest.TestCase):

    def setUp(self):
        self.secret = "secret_key"
        self.payload = {"user": "test", "role": "admin"}
        self.password = "123456"

    def test_jwt_generation_and_decoding(self):
        token = jwt_utils.generate_jwt(self.payload, self.secret, exp_minutes=1)
        decoded = jwt_utils.decode_jwt(token, self.secret)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded['user'], self.payload['user'])

    def test_password_hashing_and_verification(self):
        hashed = hashing.hash_password(self.password)
        self.assertTrue(hashing.verify_password(self.password, hashed))
        self.assertFalse(hashing.verify_password("wrongpass", hashed))

    def test_token_generation(self):
        token = tokens.generate_random_token(32)
        uuid_token = tokens.generate_uuid_token()
        self.assertEqual(len(token), 32)
        self.assertTrue(uuid_token)

    def test_time_utils(self):
        utc_now = time_utils.get_current_utc_timestamp()
        self.assertIn("T", utc_now)

    def test_success_response(self):
        resp, code = responses.success_response({"key": "value"}, "OK", 200)
        self.assertEqual(resp['status'], "success")
        self.assertEqual(code, 200)

    def test_error_response(self):
        resp, code = responses.error_response("Error", 400)
        self.assertEqual(resp['status'], "error")
        self.assertEqual(code, 400)

if __name__ == '__main__':
    unittest.main()

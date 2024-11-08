import time
import struct
import base64
import hashlib
import hmac
from twilightchat.types import User

class Token:
    def __init__(self, user: User, token_secret: str):
        self.token = self._create_token(self, user, token_secret)

    @staticmethod
    def _encode_snowflake(self, snowflake_id):
        snowflake_bytes = str(snowflake_id).encode('utf-8')
        encoded_snowflake = base64.urlsafe_b64encode(snowflake_bytes).decode('utf-8').rstrip('=')
        return encoded_snowflake

    @staticmethod
    def _generate_token_part_2(self):
        timestamp_ms = int(time.time() * 1000)
        transformed_time = (timestamp_ms // 1000) - 1293840
        token_part_2 = struct.pack('>I', transformed_time)
        return base64.urlsafe_b64encode(token_part_2).decode('utf-8').rstrip('=')

    @staticmethod
    def _generate_part_one(self, snowflake_id):
        part_1 = self._encode_snowflake(self, snowflake_id)
        part_2 = self._generate_token_part_2(self)
        return f"{part_1}.{part_2}"

    @staticmethod
    def _generate_hmac(self, key, message):
        return hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha3_224).digest()

    @staticmethod
    def _encode_hmac(self, hmac_value):
        return base64.urlsafe_b64encode(hmac_value).decode('utf-8').rstrip('=')

    @staticmethod
    def _create_token(self, user: User, token_secret: str):
        part_one = self._generate_part_one(self, user.id)
        key = f"{token_secret}--{user.password.decode('utf-8')}"
        encrypted_auth = self._generate_hmac(self, key, part_one)
        encoded_hmac = self._encode_hmac(self, encrypted_auth)
        return f"{part_one}.{encoded_hmac}"

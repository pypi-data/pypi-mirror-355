import json
import logging
from requests import session
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from rsa import decrypt, PrivateKey
from base64 import b64decode


class AccessControl:
    def __init__(self, url, uuid_key, secret_b, module_pk="", module_sk="", logger=logging):
        self._url = url
        self._log = logger
        self._uuid_key = uuid_key
        self._secret_b = secret_b
        self._module_pk = module_pk
        self._module_sk = module_sk

    def get_backend_data(self, origin):
        with session() as s:
            params = {}
            if self._module_pk and self._module_sk:
                params = {
                    "module_pk": self._module_pk,
                    "module_sk": self._module_sk
                }

            response = s.post(
                url=self._url,
                json={
                    'key': self._uuid_key
                },
                headers={
                    'Origin': origin,
                },
                params=params
            )
            if response.status_code == 200:
                encrypted_data = response.json()
                data = {}
                if isinstance(encrypted_data, dict):
                    data.update(
                        json.loads(
                            self._decrypt_data(encrypted_data)
                        )
                    )
                else:
                    for encrypt in encrypted_data:
                        data.update(
                            json.loads(
                                self._decrypt_data(encrypt)
                            )
                        )
                return data
            else:
                self._log.error(response)

    def _decrypt_data(self, data):
        rsa_private_key = bytes(self._decryption(
            data['a']
        ), 'utf-8')

        c = data['c'].encode()

        private_key = PrivateKey.load_pkcs1(rsa_private_key)

        result = decrypt(b64decode(c), private_key)

        config_data = self._decryption(result.decode() + data["b"])

        return config_data

    def _decryption(self, ciphertext):
        b_uuid_key = bytes(self._uuid_key, 'utf-8')
        b_secret_b = bytes(self._secret_b, 'utf-8')
        cipher = AES.new(b_uuid_key, AES.MODE_CBC, b_secret_b)
        return unpad(cipher.decrypt(b64decode(ciphertext)), 16).decode()

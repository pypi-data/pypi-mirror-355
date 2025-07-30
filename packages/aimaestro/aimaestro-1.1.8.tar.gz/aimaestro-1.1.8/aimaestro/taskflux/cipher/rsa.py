# -*- encoding: utf-8 -*-
import base64
from typing import IO, overload, Union

from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.PublicKey import RSA
from Cryptodome import Random

__all__ = ['generate_keys', 'decrypt', 'encrypt']

_key_size = 2048


def _encrypt(plaintext: str, public_key: RSA.RsaKey) -> str:
    """
     Encrypt plaintext using public key.
     :param plaintext: plaintext to be encrypted
     :param public_key: public key used for encryption
     :return: encrypted text in base64-encoded string format
    """
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(plaintext.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')


def _decrypt(ciphertext: str, private_key: RSA.RsaKey) -> str:
    """
    Decrypt ciphertext using private key.
    :param ciphertext: ciphertext to be decrypted
    :param private_key: private key used for decryption
    :return: decrypted text in base64-encoded string format
    """
    cipher = PKCS1_v1_5.new(private_key)
    decoded = base64.b64decode(ciphertext)
    decrypted = cipher.decrypt(decoded, None)
    return decrypted.decode('utf-8')


def generate_keys(key_size: int = _key_size) -> tuple[bytes, bytes]:
    """
    Generate random keys.
    :param key_size: key size in bits
    :return: tuple of public key and private key in bytes
    """
    random_generator = Random.new().read
    private_key = RSA.generate(key_size, random_generator)
    public_key = private_key.publickey()
    return public_key.export_key(), private_key.export_key()


@overload
def decrypt(ciphertext: str, private_key: RSA.RsaKey) -> str: ...


@overload
def decrypt(ciphertext: str, private_key: bytes) -> str: ...


@overload
def decrypt(ciphertext: str, private_key: str) -> str: ...


@overload
def decrypt(ciphertext: str, private_key: IO[bytes]) -> str: ...


def decrypt(ciphertext: str, private_key: Union[RSA.RsaKey, bytes, str, IO[bytes]]) -> str:
    """
    Decrypt ciphertext using private key.
    :param ciphertext: ciphertext to be decrypted
    :param private_key: private key used for decryption
    :return: decrypted text in base64-encoded string format
    """
    if isinstance(private_key, RSA.RsaKey):
        return _decrypt(ciphertext, private_key)
    elif isinstance(private_key, bytes):
        key = RSA.import_key(private_key)
        return _decrypt(ciphertext, key)
    elif isinstance(private_key, str):
        key = RSA.import_key(base64.b64decode(private_key.encode('utf-8')))
        return _decrypt(ciphertext, key)
    elif hasattr(private_key, 'read'):
        key_data = private_key.read()
        key = RSA.import_key(key_data)
        return _decrypt(ciphertext, key)
    else:
        raise ValueError("Unsupported private key format")


@overload
def encrypt(plaintext: str, public_key: RSA.RsaKey) -> str: ...


@overload
def encrypt(plaintext: str, public_key: bytes) -> str: ...


@overload
def encrypt(plaintext: str, public_key: str) -> str: ...


@overload
def encrypt(plaintext: str, public_key: IO[bytes]) -> str: ...


def encrypt(plaintext: str, public_key: Union[RSA.RsaKey, bytes, str, IO[bytes]]) -> str:
    """
    Encrypt plaintext using public key.
    :param plaintext: plaintext to be encrypted
    :param public_key: public key used for encryption
    :return: encrypted text in base64-encoded string format
    """
    if isinstance(public_key, RSA.RsaKey):
        return _encrypt(plaintext, public_key)
    elif isinstance(public_key, bytes):
        key = RSA.import_key(public_key)
        return _encrypt(plaintext, key)
    elif isinstance(public_key, str):
        key = RSA.import_key(base64.b64decode(public_key.encode('utf-8')))
        return _encrypt(plaintext, key)
    elif hasattr(public_key, 'read'):
        key_data = public_key.read()
        key = RSA.import_key(key_data)
        return _encrypt(plaintext, key)
    else:
        raise ValueError("Unsupported public key format")

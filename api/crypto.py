# models.py
from cryptography.fernet import Fernet
import os
import logging
from django.core.exceptions import ImproperlyConfigured

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_encryption_key():
    """
    Получает ключ шифрования из переменной окружения FERNET_KEY.
    Должен быть валидным base64-закодированным 32-байтовым ключом.
    """
    key = os.getenv('FERNET_KEY')
    if not key:
        raise ImproperlyConfigured(
            "FERNET_KEY не найден в переменных окружения.")
    return key.encode()


def encrypt_token(decripted_token):
    """Шифрует токен с помощью Fernet."""""
    f = Fernet(get_encryption_key())
    logger.debug(f"токен до шифрования: {decripted_token}")
    encrypted_token = f.encrypt(decripted_token.encode('utf-8'))
    encrypted_token_decode = encrypted_token.decode('utf-8')
    logger.debug(f"токен после шифрования: {encrypted_token_decode}")
    return encrypted_token_decode


def decrypt_token(encrypted_token):
    """Расшифровывает токен с помощью Fernet."""""
    f = Fernet(get_encryption_key())
    decripted_token = f.decrypt(encrypted_token.encode('utf-8'))
    return decripted_token.decode('utf-8')

from cryptography.fernet import Fernet
from app.core.config import get_settings

settings = get_settings()

fernet = Fernet(settings.encryption_key.encode())


def encrypt_value(value: str) -> str:
    """
    Encrypt a string value using Fernet.
    """
    encrypted = fernet.encrypt(value.encode())
    return encrypted.decode()


def decrypt_value(value: str) -> str:
    """
    Decrypt a previously encrypted value.
    """
    decrypted = fernet.decrypt(value.encode())
    return decrypted.decode()
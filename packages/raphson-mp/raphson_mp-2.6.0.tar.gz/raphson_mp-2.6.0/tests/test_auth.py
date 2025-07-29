import random
import secrets

from raphson_mp import auth


def test_hash():
    password = secrets.token_urlsafe(random.randint(0, 100))
    notpassword = secrets.token_urlsafe(random.randint(0, 100))
    hash = auth._hash_password(password)
    assert auth._verify_hash(hash, password)
    assert not auth._verify_hash(hash, notpassword)

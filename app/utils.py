from passlib.hash import md5_crypt
from random import randint

def generate_random_token() -> str:

    token = ""
    for i in range(6):
        token += str(randint(0,9))
    return md5_crypt.hash(token)

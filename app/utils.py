from random import randint

def generate_random_token() -> str:

    token = ""
    for i in range(6):
        token += str(randint(0,9))
    return token

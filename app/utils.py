from random import randint

def generate_random_token() -> str:
    token = ""
    for i in range(6):
        token += str(randint(0,9))
    return token

VALID_USERNAME = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;="
VALID_FULLNAME =  "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"

def has_valid_username_characters(username  : str):
    for i in username:
        if i not in VALID_USERNAME:
            return False
    return True

def has_valid_name_charaters(name):
    for i in name:
        if i not in VALID_FULLNAME:
            return False
    return True

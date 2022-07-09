from validate_email import validate_email
from app.auth_models import User
from app.utils import has_valid_username_characters,has_valid_name_charaters

def email_validation(context : dict , email : str) -> dict:
    if email=="" or email is None:
        context["email_required_error"] = True
        return context
    if not validate_email(email):
        context["invalid_email_error"]  = True
    elif User.query.filter_by(email=email).first():
        context["unique_email_error"] = True
    return context

def username_validation(context:dict, username : str) -> dict:
    if username == "" or username is None:
        context["username_required_error"] = True
        return context

    if len(username) > 50:
        context["username_too_long_error"] = True

    elif User.query.filter_by(username = username).first():
        context["unique_username_error"] = True
    elif not has_valid_username_characters(username):
        context["valid_characters_username_error"] = True
    return context
        
def password_validation(context:dict, p1:str, p2:str) -> dict:
    if len(p1) < 8 or len(p1) is None:
        context["weak_password_error"] = True
    elif p1 != p2:
        context["passwords_dont_match_error"] = True
    return context

def name_validation(context:dict, fname, lname)->dict:
    if fname != "" and fname is not None:
        if not has_valid_name_charaters(fname):
            context["valid_fname_error"] = True
        
    if lname != "" and lname is not None:
            if not has_valid_name_charaters(lname):
                context["valid_lname_error"] = True
    return context

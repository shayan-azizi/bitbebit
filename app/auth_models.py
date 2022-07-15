from app.extensions import db, oauth
from passlib.hash import sha256_crypt

class User(db.Model):
    _id = db.Column(db.Integer , nullable = False , primary_key = True)

    username = db.Column(db.String(50) , nullable = False , unique = True)
    email = db.Column(db.String(1000) , nullable = True   , unique = True)
    password = db.Column(db.String(100) , nullable = True)
    first_name = db.Column(db.String(50) , nullable = True)
    last_name = db.Column(db.String(50) , nullable = True)
    
    access_token = db.Column(db.String(500) , nullable = True)
    github_id = db.Column(db.String(500) , nullable = True)
    github_url = db.Column(db.String(50),nullable = True)


    def __init__(self , username ,email,  password = None , first_name=None , last_name=None ,  access_token = None, github_id = None):

        self.username = username
        if password is not None:
            self.password = sha256_crypt.hash(password)
        else:
            self.password = None
        self.first_name = None if first_name == "" else first_name
        self.last_name = None if last_name == "" else last_name
        self.email = email
        self.access_token = access_token
        self.github_id = github_id
        
        if self.github_id:
            self.github_url = self.get_github_profile_url()

    def __repr__(self):
        return f"{self._id} : {self.username} : {self.email}"

    def generate_access_token_for_sending(self):
        k = {"token_type" : "bearer" , "scope" : ""}
        k["access_token"] = self.access_token
        return k

    def get_full_name(self):
        if self.first_name == None and self.last_name == None:
            return None
        return "" if self.first_name == None else self.first_name + "" if self.last_name == None else self.last_name

    def get_github_profile_url(self):
        github = oauth.create_client("github")
        user_data = github.get("user", token = self.generate_access_token_for_sending()).json()
        username =  user_data.get("login")
        return f"https://github.com/{username}"



class NewsLetterEmails(db.Model):

    _id = db.Column(db.Integer , nullable = False , primary_key = True)
    email = db.Column(db.String(100) , nullable = False , unique = True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return self.email
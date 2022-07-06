from app.extensions import db
from passlib.hash import sha256_crypt

class User(db.Model):
    _id = db.Column(db.Integer , nullable = False , primary_key = True)

    username = db.Column(db.String(50) , nullable = False , unique = True)
    email = db.Column(db.String(1000) , nullable = False   , unique = True)
    password = db.Column(db.String(100) , nullable = False)

    first_name = db.Column(db.String(50) , nullable = True)
    last_name = db.Column(db.String(50) , nullable = True)
    send_emails = db.Column(db.Boolean , nullable = False , default = False)


    def __init__(self , username , password ,email, first_name=None , last_name=None , send_emails = False):

        self.username = username
        self.password = sha256_crypt.hash(password)
        self.first_name = None if first_name == "" else first_name
        self.last_name = None if last_name == "" else last_name
        self.email = email
        self.send_emails = send_emails

    def __repr__(self):
        return f"{self._id} : {self.username} : {self.email}"

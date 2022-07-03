from app.extensions import db

class User(db.Model):
    _id = db.Column(db.Integer , nullable = False , primary_key = True)

    username = db.Column(db.String(50) , nullable = False)
    email = db.Column(db.String(1000) , nullable = False )
    password = db.Column(db.String(100) , nullable = False)

    first_name = db.Column(db.String(50) , nullable = True)
    last_name = db.Column(db.String(50) , nullable = True)



    

    def __init__(self , username , password ,email, first_name=None , last_name=None):

        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def __repr__(self):
        return f"{self._id} : {self.username} : {self.email}"


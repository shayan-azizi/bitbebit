from flask import Flask
from app.extensions import db , csrf
from app.views import views
from app.auth import auth
from dotenv import load_dotenv
import os
load_dotenv()

def create_app():
    global db
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.register_blueprint(views , url_prefix = "")
    app.register_blueprint(auth , url_prefix = "")

    db.init_app(app=app)
    csrf.init_app(app=app)

    with app.app_context():
        db.create_all()    
        
    return app

from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

db = SQLAlchemy()
csrf = CSRFProtect()
sess = Session()
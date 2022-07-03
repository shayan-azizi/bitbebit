from flask import Blueprint , render_template
from app.extensions import db



views = Blueprint("views" , __name__ , template_folder="templates", static_folder="static")

@views.route("/")
def index():
    return render_template("index.html")


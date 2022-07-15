from flask import (
    Blueprint,
    render_template,
    abort

)
from app.auth_models import User

account = Blueprint("account" , __name__ , template_folder="templates" , static_folder="static")

@account.route("/change_profile")
def change_profile ():
    return render_template("change_profile.html")




@account.route("/profile/<username>")
def profile (username):
    user = User.query.filter_by(username = username).first()
    if user:
        return render_template("profile.html",user=user)
    abort(404)




from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    request,
    url_for,

)

account = Blueprint("account" , __name__ , template_folder="templates" , static_folder="static")

@account.route("/change_profile")
def change_profile ():
    return render_template("change_profile.html")


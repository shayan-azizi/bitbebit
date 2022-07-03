from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    session,
    request,
)
from validate_email import validate_email
from app.auth_models import User
from app.extensions import db

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

@auth.route("/signup" , methods = ["GET" , "POST"])
def signup():

    if request.method == "POST":
        context = {}

        username = request.form.get("username" , False)
        password1 = request.form.get("password1" , False)
        password2 = request.form.get("password2" , False)
        email = request.form.get("email" , False)
        fname = request.form.get("first_name" , False)
        lname = request.form.get("lname" , False)

        if request.form.get("email" , False):
            if not validate_email(request.form.get("email")):
                context["email_err"] = True
        if len(password1) < 10:
            context["weak_password"] = True
        elif password1 != password2:
            context["password_error"] = True
        if len(username) > 50:
            context["username_err"] = True
        
        else:
            if User.query.filter_by(username = username).first():
                context["user_error"] = True
        
        if context == {}:
        
            user = User(username , password1, email , fname if fname else "" , lname if lname else "")

            db.session.add(user)
            db.session.commit()

            session.clear()
            session["user_id"] = user._id
            return redirect("/")
        return render_template("signup.html" , **context)
    if request.method == "GET":
        return render_template("signup.html")



@auth.route("/login")
def login():
    
    if request.method == "POST":
        session.clear()
        username = request.form.get("username" , False)
        password = request.form.get("password" , False)

        user = User.query.filter_by(username = "username").first()
        if user and user.password  == password:
            session["user_id"] = user._id
            return redirect("/")
        flash("اطلاعات وارد شده صحت ندارد")        
        return redirect("/login")

    if request.method == "GET":
        return render_template("login.html")
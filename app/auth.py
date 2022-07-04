from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    session,
    request,
    url_for,
    jsonify
)
from datetime import timedelta
from validate_email import validate_email
import smtplib
from app.auth_models import User
from app.extensions import db
from .utils import generate_random_token
from dotenv import load_dotenv
import os
import threading

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

load_dotenv()


def send_email(to , token : str):

    gmail_server = smtplib.SMTP("smtp.gmail.com" , 587) 
    gmail_server.starttls()
    gmail_server.login(user=os.getenv("GMAIL_ADDRESS"),password=os.getenv("GMAIL_PASSWORD"))
    gmail_server.sendmail(from_addr=os.getenv("GMAIL_ADDRESS"),to_addrs=to,msg="hi!")



@auth.route("/signup" , methods = ["GET" , "POST"])
def signup():

    if request.method == "POST":
        session.clear()
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
            elif User.query.filter_by(email = email).first():
                context["email_rep_error"] = True
        else:
            context["email_err"] = True
        if len(password1) < 8:
            context["weak_password"] = True
        elif password1 != password2:
            context["password_error"] = True
        if len(username) > 50:
            context["username_err"] = True
        elif len(username) == 0:
            context["username_empty_error"] = True        
        else:
            if User.query.filter_by(username = username).first():
                context["user_error"] = True
        
        if context == {}:
            
            session["user_info_email_verif"] =  jsonify(User(username = username , password = password1 , email = email , first_name= fname , last_name=lname))
            session["verif_token"] = generate_random_token()

            threading.Thread(target=send_email , args=(email,session["verif_token"])).start()
            
            flash("ایمیل فرستادیم برات داوپش گل")
            return redirect("/email_verification")
        return render_template("signup.html" , **context)

    if request.method == "GET":
        return render_template("signup.html")



@auth.route("/login" , methods = ["GET" , "POST"])
def login():
    
    if request.method == "POST":
        session.clear()
        username = request.form.get("username" , False)
        password = request.form.get("password" , False)

        user = User.query.filter_by(username = username).first()
        if user and user.password  == password:
            session["user_id"] = user._id
            return redirect("/")
        flash("اطلاعات وارد شده صحت ندارد")        
        return redirect("/login")

    if request.method == "GET":
        return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@auth.route("/email_verification" , methods = ["GET" , "POST"])
def email_verification():
    if session.get("user_info_email_verif" , False):
        if request.method == "POST":
            token = request.form.get("token" , False)
            user_obj = session.get("user_info_email_verif")
            if token == session.get("verif_token" , False):
                db.session.add(user_obj)
                db.session.commit(user_obj)
                session.clear()
                session["user_id"] = user_obj._id
                return redirect("/")
            flash("کد درست نیست")
            return redirect("/email_verification")
        elif request.method == "GET":
            return render_template("email_verficiation.html")
    return redirect(url_for("auth.signup"))

    
@auth.route("/test")
def test():
    return f"{session.items()}" ,200


@auth.route("/loggedin")
def loggedin():
    return f"{session.get('user_id' , False)}"

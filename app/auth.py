from pipes import Template
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    session,
    request,
    url_for,

)
from validate_email import validate_email
import smtplib
from app.auth_models import User
from app.extensions import db
from .utils import generate_random_token
from dotenv import load_dotenv
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

load_dotenv()


def send_email(to , token : str):

    message = MIMEMultipart("alternative")
    message["subject"] = "کد تایید"
    message["TO"] = to
    message["FROM"] = os.getenv("GMAIL_ADDRESS")
    
    env = Environment(loader = PackageLoader("app"),autoescape=select_autoescape())

    template = env.get_template("ver_email_template.html")
    HTML_BODY = MIMEText(template.render(token = token), 'html')
    message.attach(HTML_BODY)


    gmail_server = smtplib.SMTP("smtp.gmail.com" , 587) 
    gmail_server.starttls()
    gmail_server.login(user=os.getenv("GMAIL_ADDRESS"),password=os.getenv("GMAIL_PASSWORD"))
    gmail_server.sendmail(from_addr=os.getenv("GMAIL_ADDRESS"),to_addrs=to,msg=message.as_string())



@auth.route("/signup" , methods = ["GET" , "POST"])
def signup():

    if request.method == "POST":
        session.clear()
        session.permanent = True
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
            
            session["user_info_email_verif"] =  {
                "username" : username,
                "password" : password1,
                "email" : email,
                "fname" : fname,
                "lname" : lname,
                "token" : generate_random_token()
            }

            threading.Thread(target=send_email , args=(email,session["user_info_email_verif"]["token"])).start()
            
            flash("ایمیل فرستادیم برات داوپش گل")
            return redirect("/email_verification")
        return render_template("signup.html" , **context)

    if request.method == "GET":
        return render_template("signup.html")



@auth.route("/login" , methods = ["GET" , "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username" , False)
        password = request.form.get("password" , False)

        user = User.query.filter_by(username = username).first()
        if user and user.password  == password:
            session["user_id"] = user._id
            return redirect("/")

        session.clear()
        session.permanent = True
        flash("اطلاعات وارد شده صحت ندارد")        
        return redirect("/login")

    if request.method == "GET":
        return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    session.permanent = True
    return redirect("/")

@auth.route("/email_verification" , methods = ["GET" , "POST"])
def email_verification():
    if session.get("user_info_email_verif" , False):
        if request.method == "POST":
            sess_token = session["user_info_email_verif"]["token"]
            token = request.form.get("token" , False)
            user_info = session["user_info_email_verif"]
            if token == sess_token:
                user_obj = User(user_info["username"] , password=user_info["password"] , email = user_info["email"] , first_name=user_info["fname"] , last_name=user_info["lname"])
                db.session.add(user_obj)
                db.session.commit()
                session.clear()
                session.permanent = True
                session["user_id"] = user_obj._id
                return redirect("/")
            flash("کد درست نیست")
            return redirect("/email_verification")
        elif request.method == "GET":
            return render_template("email_verification.html")
    return redirect(url_for("auth.signup"))

    
@auth.route("/test")
def test():
    return f"{session.items()}" ,200


@auth.route("/loggedin")
def loggedin():    
    return f"{session.get('user_id' , False)}"

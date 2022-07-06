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
from validate_email import validate_email
import smtplib
from app.auth_models import User
from app.extensions import db
from .utils import generate_random_token, has_valid_username_characters , has_valid_name
from dotenv import load_dotenv
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape
from passlib.hash import sha256_crypt

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

load_dotenv()


def is_logged_in():
    return True if session.get("user_id" , False) else False


@auth.before_app_request
def handle_sessions():
    if is_logged_in():
        current_app.permanent_session_lifetime = 24 * 60 * 60 * 7 * 2 #2 weeks
    else:
        current_app.permanent_session_lifetime = 15 * 60 #15 minutes


def login_user(user : User):

    session.clear()
    session.permanent = True
    session["user_id"] = user._id
    current_app.permanent_session_lifetime = 24 * 60 * 60 * 7


def send_email(to , token : str , username):

    message = MIMEMultipart("alternative")
    message["subject"] = "کد تایید"
    message["TO"] = to
    message["FROM"] = os.getenv("GMAIL_ADDRESS")
    
    env = Environment(loader = PackageLoader("app"),autoescape=select_autoescape())

    template = env.get_template("ver_email_template.html")
    HTML_BODY = MIMEText(template.render(token = token , username=username), 'html')
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
        fname = request.form.get("first_name" , None)
        lname = request.form.get("last_name" ,   None)
        send_emails = True if request.form.get("send_emails" , False)=="" else False

        #Email Validation
        if request.form.get("email" , False):
            if not validate_email(request.form.get("email")):
                context["invalid_email_error"] = True
            elif User.query.filter_by(email = email).first():
                context["unique_email_error"] = True
        else:
            context["email_required_error"] = True
        
        #password Validation
        if len(password1) < 8:
            context["weak_password_error"] = True
        elif password1 != password2:
            context["passwords_dont_match_error"] = True
        
        #username Validation
        if len(username) > 50:
            context["username_too_long_error"] = True
        elif len(username) == 0:
            context["username_required_error"] = True        
        elif User.query.filter_by(username = username).first():
                context["unique_username_error"] = True
        elif not has_valid_username_characters(username):
            context["valid_characters_username_error"] = True

        #name validation
        if fname != "":
            if not has_valid_name(fname):
                context["valid_fname_error"] = True
        if lname != "":
            if not has_valid_name(lname):
                context["valid_lname_error"] = True

        
        if context == {}:
            
            session["user_info"] =  {
                "username" : username,
                "password" : password1,
                "email" : email,
                "first_name" : fname,
                "last_name" : lname,
                "send_emails" : send_emails,
            }
            session["token"] = generate_random_token()

            threading.Thread(target=send_email , args=(email,session["token"] ,session["user_info"]["username"])).start()
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
        
        if user and sha256_crypt.verify(password , user.password):
            login_user(user=user)
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
    if session.get("user_info" , False) and session.get("token" , False):
        if request.method == "POST":
            sess_token = session["token"]
            token = request.form.get("token" , False)
            
            if token == sess_token:
                user_obj = User(**session["user_info"])
                db.session.add(user_obj)
                db.session.commit()
                login_user(user_obj)
                return redirect("/")
            flash("کد درست نیست")
            return redirect("/email_verification")
        elif request.method == "GET":
            return render_template("email_verification.html")
    return redirect(url_for("auth.signup"))



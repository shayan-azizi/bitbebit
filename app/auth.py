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
import smtplib
from app.auth_models import User, NewsLetterEmails
from app.extensions import db , oauth
from .utils import generate_random_token
from dotenv import load_dotenv
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape
from passlib.hash import sha256_crypt
from app.auth_validators import *

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

load_dotenv()


#OAUTH

oauth.register(
    "github",
    client_id = "45a4c297241e2ea0dd90",
    client_secret = "499df85557bdf2d4bcedbc8a4b4e1a41ee56c711",
    access_token_url = "https://github.com/login/oauth/access_token",
    authorize_url = "https://github.com/login/oauth/authorize",
    api_base_url = "https://api.github.com/",
)

#------SOME FUNCTIONS


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
    if user.access_token is not None:
        session["user_id"] = user.github_id
    else:
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





#ROUTES
@auth.route("/signup" , methods = ["GET" , "POST"])
def signup():

    if request.method == "POST":
        session.clear()
        session.permanent = True
        context = {}

        username = request.form.get("username" , None)
        password1 = request.form.get("password1" , None)
        password2 = request.form.get("password2" , None)
        email = request.form.get("email" , None)
        fname = request.form.get("first_name" , None)
        lname = request.form.get("last_name" ,   None)
        send_emails = True if request.form.get("send_emails" , False)=="" else False

        context = email_validation(context, email)
        context = password_validation(context, password1, password2)
        context = username_validation(context, username)
        context = name_validation(context, fname, lname)
        
        if context == {}:

            db.session.add(NewsLetterEmails(email = email))
            db.session.commit()
            
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
            return redirect("/email_verification")
        return render_template("signup.html" , **context)

    if request.method == "GET":
        return render_template("signup.html")





@auth.route("/oauth/signup" , methods = ["GET" , "POST"])
def oauth_signup():
    github = oauth.create_client("github")
    redirect_uri = url_for("auth.call_back_signup" , _external = True)
    return github.authorize_redirect(redirect_uri)





@auth.route("/callback/signup" , methods = ["GET" , "POST"])
def call_back_signup():
    
    github = oauth.create_client("github")
    token = github.authorize_access_token()
    user_data = github.get("user" , token = token).json()
    print(user_data)
    email =    user_data.get("email" , False)
    email_errors = email_validation({} , email)

    if email_errors.get("email_required_error" , False):
        print("email_required_error")
        flash("")
        return redirect("/signup")
    elif email_errors.get("unique_email_error",False):
        print("unique_email_error")
        flash("")
        return redirect("/signup")


    if request.method == "POST":
        username = request.form.get("username" , None)
        username_errors = username_validation({}, username)
        if username_errors != {}:
            return render_template("username_form.html" , **username_errors)
        
        g_id = user_data.get("id" , None)
        account = User(username=username, email=email, access_token=token, github_id=g_id)
        db.session.add(account)
        db.session.commit() #TODO find a way to store dicts in db
        login_user(account)
        return redirect("/")

    if request.method == "GET":
        username = user_data.get("login" , False)
        username_errors=  username_validation({} , username)

        if username_errors.get("unique_username_error", False):
            return render_template("username_form.html")

        g_id = user_data.get("id" , None)
        account = User(username=username, email=email, access_token=token, github_id=g_id)
        db.session.add(account)
        db.session.commit()
        login_user(account)
        return redirect("/")

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
                if any([User.query.filter_by(email = session["user_info"]["email"]).first(),
                        User.query.filter_by(username=session["user_info"]["username"]).first()]):
                    session.clear()
                    session.permanent = True
                    flash("خیلی کند عمل کردید  اقای محترم یکی زودتر از شما با ایمیل یا یوزرنیم خودتون ثبت نام کرد")
                    return redirect("/signup")
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

@auth.route("/loggedin")
def loggedin():
    return f"{is_logged_in()}"
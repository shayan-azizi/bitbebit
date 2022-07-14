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
from .utils import generate_random_token, VALID_USERNAME
from dotenv import load_dotenv
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape
from passlib.hash import sha256_crypt
from app.auth_validators import *
from random import randint

auth = Blueprint("auth" , __name__ , template_folder="templates" , static_folder="static")

load_dotenv()


#OAUTH

oauth.register(
    "github",
    client_id = os.getenv("GITHUB_CLIENT_ID"),
    client_secret = os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url = "https://github.com/login/oauth/access_token",
    authorize_url = "https://github.com/login/oauth/authorize",
    api_base_url = "https://api.github.com/",
)

#------SOME FUNCTIONS


def is_logged_in():
    return True if session.get("user_id" , False) else False

def clear_session():
    session.clear()
    session.permanent = True

@auth.before_app_request
def handle_sessions():

    if is_logged_in():

        current_app.permanent_session_lifetime = 24 * 60 * 60 * 7 * 2 #2 weeks
    else:
                
        current_app.permanent_session_lifetime = 60 * 15 #15 minutes


def login_user(user : User):
    clear_session()
    if user.access_token is not None:
        session["user_id"] = user._id
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
        clear_session()
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
            if not NewsLetterEmails.query.filter_by(email = email).first() and send_emails == True:

                db.session.add(NewsLetterEmails(email = email))
                db.session.commit()
            
            session["user_info"] =  {
                "username" : username,
                "password" : password1,
                "email" : email,
                "first_name" : fname,
                "last_name" : lname,
            }
            session["token"] = generate_random_token()

            threading.Thread(target=send_email , args=(email,session["token"] ,session["user_info"]["username"])).start()
            return redirect("/email_verification")
        return render_template("signup.html" , **context)

    if request.method == "GET":
        return render_template("signup.html")


@auth.route("/oauth/signup" , methods = ["GET" , "POST"])
def oauth_signup():
    session["signup"] = True
    github = oauth.create_client("github")
    redirect_uri = url_for("auth.call_back" , _external = True)
    return github.authorize_redirect(redirect_uri)


@auth.route("/oauth/login", methods = ["GET", "POST"])
def oauth_login():
    session["login"] = True
    github = oauth.create_client("github")
    redirect_uri = url_for("auth.call_back" , _external = True)
    return github.authorize_redirect(redirect_uri)




@auth.route("/callback" , methods = ["GET"])
def call_back():
    
    if session.get("signup" , False):


        github = oauth.create_client("github")
        token = github.authorize_access_token()
        user_data = github.get("user" , token = token).json()
        email =    user_data.get("email" , False)
        username = user_data.get("login" , False)
        email_errors = email_validation({} , email)
        username_errors=  username_validation({} , username)

        if email_errors != {}:
            email = None
        if username_errors != {}:
            extra = ""
            while User.query.filter_by(username = username + extra).first():
                extra = "".join([VALID_USERNAME[randint(0,len(VALID_USERNAME)-1)] for i in range(5)])
            username += extra

        g_id = user_data.get("id" , None)
        if User.query.filter_by(github_id = g_id).first():
            clear_session()
            flash("اکانتی با این اکانت گیتهاب وجود دارد")
            return redirect("/signup")
        account = User(username=username, email=email, access_token=token["access_token"], github_id=g_id)
        db.session.add(account)
        db.session.commit()
        login_user(account)
        return redirect("/")

    if session.get("login", False):
        github = oauth.create_client("github")
        token = github.authorize_access_token()
        g_id = github.get("user",token=token).json()["id"]
        if User.query.filter_by(github_id=g_id).first():
            account = User.query.filter_by(github_id= g_id).first()
            account.access_token = token["access_token"]
            db.session.commit()
            login_user(account)
            return redirect("/")
        clear_session()
        flash("شما اکانتی نساختید")
        return redirect("/signup")


@auth.route("/login" , methods = ["GET" , "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username" , None)
        password = request.form.get("password" , None)

        user = User.query.filter_by(username = username).first()
        
        if user and sha256_crypt.verify(password , user.password):
            login_user(user=user)
            return redirect("/")

        clear_session()
        flash("اطلاعات وارد شده صحت ندارد")        
        return redirect("/login")

    if request.method == "GET":
        return render_template("login.html")


@auth.route("/logout")
def logout():
    clear_session()
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
                    clear_session()
                    flash("خیلی کند عمل کردید  اقای محترم یکی زودتر از شما با ایمیل یا یوزرنیم خودتون ثبت نام کرد")
                    return redirect("/signup")
                user_obj = User(**session["user_info"])
                db.session.add(user_obj)
                db.session.commit()
                login_user(user_obj)
                return redirect("/")
            clear_session()
            flash("کد درست نیست")
            return redirect("/signup")
        elif request.method == "GET":
            return render_template("email_verification.html")
    return redirect(url_for("auth.signup"))

@auth.route("/loggedin")
def loggedin():
    return f"{is_logged_in()}"

@auth.route("/test")
def test():
    return f"{session.items()}"

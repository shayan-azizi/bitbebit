from flask import Blueprint, render_template


errors = Blueprint("errors" , __name__ , template_folder="templates" , static_folder="static")

@errors.app_errorhandler(404)
def page_not_found (e):
    return render_template("404.html"), 404

@errors.app_errorhandler(405)
def page_not_found (e):
    return render_template("405.html"), 405

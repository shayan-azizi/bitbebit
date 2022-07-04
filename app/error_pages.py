from flask import Blueprint, render_template


errors = Blueprint("errors" , __name__ , template_folder="templates" , static_folder="static")


@errors.errorhandler(404)
def page_not_found (e):
    return render_template("404.html"), 404
    
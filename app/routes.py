from flask import Blueprint, render_template

main = Blueprint("main", __name__, template_folder="templates")


@main.route("/", methods=["GET"])
def index():
    print("Main blueprint loaded!")
    return render_template("index.html")

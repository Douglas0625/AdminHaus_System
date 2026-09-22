from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/admin")
def dashboard_admin():
    return render_template("dashboard_admin.html")


@dashboard_bp.route("/dashboard/gestor")
def dashboard_gestor():
    return render_template("dashboard_gestor.html")


@dashboard_bp.route("/dashboard/propietario")
def dashboard_propietario():
    return render_template("dashboard_propietario.html")
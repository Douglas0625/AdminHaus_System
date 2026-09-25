from flask import Blueprint, render_template

from app.security import roles_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/admin")
@roles_required("ADMINISTRADOR")
def dashboard_admin():
    return render_template("dashboard_admin.html")


@dashboard_bp.route("/dashboard/gestor")
@roles_required("GESTOR")
def dashboard_gestor():
    return render_template("dashboard_gestor.html")


@dashboard_bp.route("/dashboard/propietario")
@roles_required("PROPIETARIO")
def dashboard_propietario():
    return render_template("dashboard_propietario.html")
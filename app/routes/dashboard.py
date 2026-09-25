from flask import Blueprint, render_template

from app.services.dashboard_service import (
    get_staff_dashboard,
    get_owner_dashboard
)
from app.security import roles_required, usuario_activo


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/admin")
@roles_required("ADMINISTRADOR")
def dashboard_admin():

    dashboard = get_staff_dashboard()

    return render_template(
        "dashboard_admin.html",
        **dashboard
    )


@dashboard_bp.route("/dashboard/gestor")
@roles_required("GESTOR")
def dashboard_gestor():

    dashboard = get_staff_dashboard()

    return render_template(
        "dashboard_gestor.html",
        **dashboard
    )


@dashboard_bp.route("/dashboard/propietario")
@roles_required("PROPIETARIO")
def dashboard_propietario():

    usuario = usuario_activo()

    dashboard = get_owner_dashboard(usuario.id)

    if dashboard is None:
        return "El usuario no tiene un propietario asociado.", 404

    return render_template(
        "dashboard_propietario.html",
        **dashboard
    )
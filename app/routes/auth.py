from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash

from app.models.usuario import Usuario


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("usuario", "").strip()
        password = request.form.get("contrasena", "")

        if not username or not password:
            return render_template(
                "login.html",
                error="Debes ingresar usuario y contraseña."
            )

        usuario = Usuario.query.filter_by(username=username).first()

        if (
            usuario is None
            or not usuario.activo
            or not check_password_hash(usuario.password_hash, password)
        ):
            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos."
            )

        # Limpiamos cualquier sesión anterior
        session.clear()

        # Guardamos únicamente la información necesaria
        session["usuario_id"] = usuario.id
        session["username"] = usuario.username
        session["rol"] = usuario.rol

        # Redirección según el rol
        if usuario.rol == "ADMINISTRADOR":
            return redirect(url_for("dashboard.dashboard_admin"))

        if usuario.rol == "GESTOR":
            return redirect(url_for("dashboard.dashboard_gestor"))

        if usuario.rol == "PROPIETARIO":
            return redirect(url_for("dashboard.dashboard_propietario"))

        session.clear()

        return render_template(
            "login.html",
            error="El usuario tiene un rol no válido."
        )

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))
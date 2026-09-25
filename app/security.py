from functools import wraps

from flask import abort, redirect, session, url_for

from app import db
from app.models.usuario import Usuario


def usuario_activo():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return None

    usuario = db.session.get(Usuario, usuario_id)

    if usuario is None or not usuario.activo:
        session.clear()
        return None

    return usuario


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        usuario = usuario_activo()

        if usuario is None:
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*roles):
    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            usuario = usuario_activo()

            if usuario is None:
                return redirect(url_for("auth.login"))

            if usuario.rol not in roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator
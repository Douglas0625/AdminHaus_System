from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.security import roles_required, usuario_activo

from app.services.usuario_service import (
    obtener_usuarios,
    obtener_usuario,
    obtener_propietarios_disponibles,
    crear_usuario,
    actualizar_usuario,
    cambiar_estado as cambiar_estado_usuario,
)


usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


# =========================================================
# LISTAR USUARIOS
# =========================================================

@usuarios_bp.route("/")
@roles_required("ADMINISTRADOR")
def lista():

    buscar = request.args.get("buscar", "").strip()
    rol = request.args.get("rol", "todos")
    estado = request.args.get("estado", "todos")

    usuarios = obtener_usuarios(buscar=buscar, rol=rol, estado=estado)

    return render_template(
        "usuarios/usuarios.html",
        usuarios=usuarios,
        buscar=buscar,
        rol=rol,
        estado=estado,
    )


# =========================================================
# VER USUARIO (SOLO LECTURA)
# =========================================================

@usuarios_bp.route("/<int:usuario_id>")
@roles_required("ADMINISTRADOR")
def detalle(usuario_id):

    usuario = obtener_usuario(usuario_id)

    if usuario is None:
        return "Usuario no encontrado.", 404

    return render_template(
        "usuarios/nuevo_editar_usuario.html",
        usuario=usuario,
        form=None,
        propietarios_disponibles=[],
        modo="detalle",
    )


# =========================================================
# NUEVO USUARIO
# =========================================================

@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR")
def nuevo():

    if request.method == "POST":

        admin_actual = usuario_activo()

        usuario, errores = crear_usuario(request.form, admin_actual)

        if errores:

            for error in errores:
                flash(error, "danger")

            return render_template(
                "usuarios/nuevo_editar_usuario.html",
                usuario=None,
                form=request.form,
                propietarios_disponibles=obtener_propietarios_disponibles(),
                modo="nueva",
            )

        flash("Usuario registrado correctamente.", "success")

        return redirect(url_for("usuarios.lista"))

    return render_template(
        "usuarios/nuevo_editar_usuario.html",
        usuario=None,
        form=None,
        propietarios_disponibles=obtener_propietarios_disponibles(),
        modo="nueva",
    )


# =========================================================
# EDITAR USUARIO
# =========================================================

@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR")
def editar(usuario_id):

    usuario = obtener_usuario(usuario_id)

    if usuario is None:
        return "Usuario no encontrado.", 404

    admin_actual = usuario_activo()

    if request.method == "POST":

        ok, errores = actualizar_usuario(usuario, request.form, admin_actual)

        if errores:

            for error in errores:
                flash(error, "danger")

            return render_template(
                "usuarios/nuevo_editar_usuario.html",
                usuario=usuario,
                form=request.form,
                propietarios_disponibles=obtener_propietarios_disponibles(),
                modo="editar",
            )

        flash("Usuario actualizado correctamente.", "success")

        return redirect(url_for("usuarios.lista"))

    return render_template(
        "usuarios/nuevo_editar_usuario.html",
        usuario=usuario,
        form=None,
        propietarios_disponibles=obtener_propietarios_disponibles(),
        modo="editar",
    )


# =========================================================
# BLOQUEAR / DESBLOQUEAR
# =========================================================

@usuarios_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@roles_required("ADMINISTRADOR")
def cambiar_estado(usuario_id):

    usuario = obtener_usuario(usuario_id)

    if usuario is None:
        return "Usuario no encontrado.", 404

    admin_actual = usuario_activo()

    ok, error = cambiar_estado_usuario(usuario, admin_actual)

    if not ok:
        flash(error, "warning")
    elif usuario.activo:
        flash("El usuario fue activado.", "success")
    else:
        flash("El usuario fue bloqueado.", "warning")

    return redirect(url_for("usuarios.lista"))

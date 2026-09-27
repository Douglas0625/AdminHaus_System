from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app.security import roles_required, usuario_activo

from app.services.propiedad_service import (
    obtener_propiedades,
    obtener_propiedad,
    usuario_puede_acceder_propiedad,
    obtener_propietarios_para_select,
    crear_propiedad,
    actualizar_propiedad,
    agregar_fotografias,
    eliminar_fotografias,
)


propiedades_bp = Blueprint(
    "propiedades",
    __name__,
    url_prefix="/propiedades"
)


# =========================================================
# LISTADO (ADMINISTRADOR / GESTOR) - TODAS LAS PROPIEDADES
# =========================================================

@propiedades_bp.route("/")
@roles_required("ADMINISTRADOR", "GESTOR")
def lista():

    usuario = usuario_activo()

    buscar = request.args.get("buscar", "").strip()
    tipo = request.args.get("tipo", "todos")
    estado = request.args.get("estado", "todos")

    propiedades = obtener_propiedades(
        usuario,
        buscar=buscar,
        tipo=tipo,
        estado=estado,
    )

    return render_template(
        "propiedades/propiedades.html",
        propiedades=propiedades,
        buscar=buscar,
        tipo=tipo,
        estado=estado,
    )


# =========================================================
# LISTADO (PROPIETARIO) - SOLO SUS PROPIAS PROPIEDADES
# =========================================================

@propiedades_bp.route("/mis")
@roles_required("PROPIETARIO")
def mis_propiedades():

    usuario = usuario_activo()

    buscar = request.args.get("buscar", "").strip()
    tipo = request.args.get("tipo", "todos")
    estado = request.args.get("estado", "todos")

    propiedades = obtener_propiedades(
        usuario,
        buscar=buscar,
        tipo=tipo,
        estado=estado,
    )

    return render_template(
        "propiedades/propiedades.html",
        propiedades=propiedades,
        buscar=buscar,
        tipo=tipo,
        estado=estado,
    )


# =========================================================
# VER DETALLE
# =========================================================

@propiedades_bp.route("/<int:propiedad_id>")
@roles_required("ADMINISTRADOR", "GESTOR", "PROPIETARIO")
def detalle(propiedad_id):

    usuario = usuario_activo()

    propiedad = obtener_propiedad(propiedad_id)

    if propiedad is None:
        return "Propiedad no encontrada.", 404

    # Autorización en backend: un PROPIETARIO no puede ver el
    # detalle de una propiedad que no le pertenece, aunque
    # escriba la URL manualmente.
    if not usuario_puede_acceder_propiedad(usuario, propiedad):
        abort(403)

    return render_template(
        "propiedades/propiedades_form.html",
        propiedad=propiedad,
        form=None,
        propietarios=[],
        modo="detalle",
    )


# =========================================================
# NUEVA PROPIEDAD
# =========================================================

@propiedades_bp.route("/nueva", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def nueva():

    propietarios = obtener_propietarios_para_select()

    if request.method == "POST":

        propiedad, errores = crear_propiedad(request.form)

        if errores:

            for error in errores:
                flash(error, "danger")

            return render_template(
                "propiedades/propiedades_form.html",
                propiedad=None,
                form=request.form,
                propietarios=propietarios,
                modo="nueva",
            )

        errores_fotos = agregar_fotografias(
            propiedad,
            request.form.getlist("fotos_url"),
        )

        for error in errores_fotos:
            flash(error, "warning")

        flash("Propiedad registrada correctamente.", "success")

        return redirect(url_for("propiedades.lista"))

    return render_template(
        "propiedades/propiedades_form.html",
        propiedad=None,
        form=None,
        propietarios=propietarios,
        modo="nueva",
    )


# =========================================================
# EDITAR PROPIEDAD
# =========================================================

@propiedades_bp.route("/<int:propiedad_id>/editar", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def editar(propiedad_id):

    propiedad = obtener_propiedad(propiedad_id)

    if propiedad is None:
        return "Propiedad no encontrada.", 404

    propietarios = obtener_propietarios_para_select()

    if request.method == "POST":

        ok, errores = actualizar_propiedad(propiedad, request.form)

        if errores:

            for error in errores:
                flash(error, "danger")

            return render_template(
                "propiedades/propiedades_form.html",
                propiedad=propiedad,
                form=request.form,
                propietarios=propietarios,
                modo="editar",
            )

        eliminar_fotografias(
            propiedad,
            request.form.getlist("fotos_eliminar"),
        )

        errores_fotos = agregar_fotografias(
            propiedad,
            request.form.getlist("fotos_url"),
        )

        for error in errores_fotos:
            flash(error, "warning")

        flash("Propiedad actualizada correctamente.", "success")

        return redirect(url_for("propiedades.lista"))

    return render_template(
        "propiedades/propiedades_form.html",
        propiedad=propiedad,
        form=None,
        propietarios=propietarios,
        modo="editar",
    )

from flask import Blueprint, render_template, request, redirect, url_for, abort

from app.services.inquilino_service import (
    obtener_inquilinos,
    crear_inquilino,
    obtener_inquilino_por_id,
    actualizar_inquilino,
)


inquilinos_bp = Blueprint("inquilinos", __name__)


@inquilinos_bp.route("/inquilinos")
def inquilinos():

    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "todos")

    filas = obtener_inquilinos(buscar=buscar, estado=estado)

    return render_template(
        "inquilinos.html",
        filas=filas,
        buscar=buscar,
        estado=estado,
    )


@inquilinos_bp.route("/inquilinos/nuevo", methods=["GET", "POST"])
def nuevo_inquilino():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        dui = request.form.get("dui", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()

        _, error = crear_inquilino(nombre, apellido, dui, telefono, correo)

        if error:
            return render_template(
                "nuevo_inquilino.html",
                form=request.form,
                modo="nuevo",
                error=error,
            )

        return redirect(url_for("inquilinos.inquilinos"))

    return render_template(
        "nuevo_inquilino.html",
        form={},
        modo="nuevo",
    )


@inquilinos_bp.route("/inquilinos/<int:inquilino_id>")
def ver_inquilino(inquilino_id):

    inquilino = obtener_inquilino_por_id(inquilino_id)

    if inquilino is None:
        abort(404)

    return render_template(
        "nuevo_inquilino.html",
        form=inquilino,
        modo="ver",
    )


@inquilinos_bp.route("/inquilinos/<int:inquilino_id>/editar", methods=["GET", "POST"])
def editar_inquilino(inquilino_id):

    inquilino = obtener_inquilino_por_id(inquilino_id)

    if inquilino is None:
        abort(404)

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        dui = request.form.get("dui", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()

        ok, error = actualizar_inquilino(
            inquilino_id, nombre, apellido, dui, telefono, correo
        )

        if error:
            return render_template(
                "nuevo_inquilino.html",
                form=request.form,
                modo="editar",
                inquilino_id=inquilino_id,
                error=error,
            )

        return redirect(url_for("inquilinos.inquilinos"))

    return render_template(
        "nuevo_inquilino.html",
        form=inquilino,
        modo="editar",
        inquilino_id=inquilino_id,
    )
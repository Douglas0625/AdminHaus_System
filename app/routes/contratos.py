from flask import Blueprint, render_template, request, redirect, url_for, abort

from app.services.contrato_service import (
    obtener_contratos,
    obtener_contrato_por_id,
    crear_contrato,
    actualizar_contrato,
    obtener_propiedades_para_select,
    obtener_inquilinos_para_select,
)


contratos_bp = Blueprint("contratos", __name__)


@contratos_bp.route("/contratos")
def contratos():

    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "todos")

    filas = obtener_contratos(buscar=buscar, estado=estado)

    return render_template(
        "contratos.html",
        filas=filas,
        buscar=buscar,
        estado=estado,
    )


@contratos_bp.route("/contratos/nuevo", methods=["GET", "POST"])
def nuevo_contrato():

    propiedades = obtener_propiedades_para_select()
    inquilinos = obtener_inquilinos_para_select()

    if request.method == "POST":

        propiedad_id = request.form.get("propiedad_id", "").strip()
        inquilino_id = request.form.get("inquilino_id", "").strip()
        fecha_inicio = request.form.get("fecha_inicio", "").strip()
        fecha_fin = request.form.get("fecha_fin", "").strip()
        monto_mensual = request.form.get("monto_mensual", "").strip()
        deposito = request.form.get("deposito", "").strip()
        dia_pago = request.form.get("dia_pago", "").strip()

        _, error = crear_contrato(
            propiedad_id or None,
            inquilino_id or None,
            fecha_inicio or None,
            fecha_fin or None,
            monto_mensual or None,
            deposito or None,
            dia_pago or None,
        )

        if error:
            return render_template(
                "nuevo_contrato.html",
                form=request.form,
                modo="nuevo",
                error=error,
                propiedades=propiedades,
                inquilinos=inquilinos,
            )

        return redirect(url_for("contratos.contratos"))

    return render_template(
        "nuevo_contrato.html",
        form={},
        modo="nuevo",
        propiedades=propiedades,
        inquilinos=inquilinos,
    )


@contratos_bp.route("/contratos/<int:contrato_id>")
def ver_contrato(contrato_id):

    contrato = obtener_contrato_por_id(contrato_id)

    if contrato is None:
        abort(404)

    return render_template(
        "nuevo_contrato.html",
        form=contrato,
        modo="ver",
        propiedades=[],
        inquilinos=[],
    )


@contratos_bp.route("/contratos/<int:contrato_id>/editar", methods=["GET", "POST"])
def editar_contrato(contrato_id):

    contrato = obtener_contrato_por_id(contrato_id)

    if contrato is None:
        abort(404)

    propiedades = obtener_propiedades_para_select()
    inquilinos = obtener_inquilinos_para_select()

    if request.method == "POST":

        propiedad_id = request.form.get("propiedad_id", "").strip()
        inquilino_id = request.form.get("inquilino_id", "").strip()
        fecha_inicio = request.form.get("fecha_inicio", "").strip()
        fecha_fin = request.form.get("fecha_fin", "").strip()
        monto_mensual = request.form.get("monto_mensual", "").strip()
        deposito = request.form.get("deposito", "").strip()
        dia_pago = request.form.get("dia_pago", "").strip()
        estado = request.form.get("estado", "").strip()

        ok, error = actualizar_contrato(
            contrato_id,
            propiedad_id or None,
            inquilino_id or None,
            fecha_inicio or None,
            fecha_fin or None,
            monto_mensual or None,
            deposito or None,
            dia_pago or None,
            estado or None,
        )

        if error:
            return render_template(
                "nuevo_contrato.html",
                form=request.form,
                modo="editar",
                contrato_id=contrato_id,
                error=error,
                propiedades=propiedades,
                inquilinos=inquilinos,
            )

        return redirect(url_for("contratos.contratos"))

    return render_template(
        "nuevo_contrato.html",
        form=contrato,
        modo="editar",
        contrato_id=contrato_id,
        propiedades=propiedades,
        inquilinos=inquilinos,
    )
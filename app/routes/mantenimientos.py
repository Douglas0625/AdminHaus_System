from flask import Blueprint, render_template, request, redirect, url_for, abort, session

from app.security import roles_required

from app.services.mantenimiento_service import (
    obtener_mantenimientos,
    obtener_mantenimiento_por_id,
    crear_mantenimiento,
    actualizar_mantenimiento,
    obtener_propiedades_para_select,
    obtener_proveedores_para_select,
    propietario_tiene_acceso_mantenimiento,
)


mantenimientos_bp = Blueprint("mantenimientos", __name__)


def _usuario_id_propietario_actual():
    """
    Devuelve el id del usuario si es PROPIETARIO (para filtrar), o
    None si es ADMINISTRADOR o GESTOR (sin filtro por ahora, hasta
    que se agregue gestor_id a la tabla propiedad).
    """
    if session.get("rol") == "PROPIETARIO":
        return session.get("usuario_id")
    return None


@mantenimientos_bp.route("/mantenimientos")
@roles_required("ADMINISTRADOR", "GESTOR", "PROPIETARIO")
def mantenimientos():

    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "todos")

    filas = obtener_mantenimientos(
        buscar=buscar,
        estado=estado,
        usuario_id_propietario=_usuario_id_propietario_actual(),
    )

    return render_template(
        "mantenimientos.html",
        filas=filas,
        buscar=buscar,
        estado=estado,
    )


def _leer_formulario():
    return {
        "propiedad_id": request.form.get("propiedad_id", "").strip() or None,
        "proveedor_id": request.form.get("proveedor_id", "").strip() or None,
        "categoria": request.form.get("categoria", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
        "fecha_solicitud": request.form.get("fecha_solicitud", "").strip() or None,
        "estado": request.form.get("estado", "").strip(),
        "costo": request.form.get("costo", "").strip() or None,
        "observaciones": request.form.get("observaciones", "").strip() or None,
    }


@mantenimientos_bp.route("/mantenimientos/nuevo", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def nueva_solicitud():

    propiedades = obtener_propiedades_para_select()
    proveedores = obtener_proveedores_para_select()

    if request.method == "POST":

        datos = _leer_formulario()

        _, error = crear_mantenimiento(**datos)

        if error:
            return render_template(
                "nueva_solicitud.html",
                form=request.form,
                modo="nuevo",
                error=error,
                propiedades=propiedades,
                proveedores=proveedores,
            )

        return redirect(url_for("mantenimientos.mantenimientos"))

    return render_template(
        "nueva_solicitud.html",
        form={"estado": "PENDIENTE"},
        modo="nuevo",
        propiedades=propiedades,
        proveedores=proveedores,
    )


@mantenimientos_bp.route("/mantenimientos/<int:mantenimiento_id>")
@roles_required("ADMINISTRADOR", "GESTOR", "PROPIETARIO")
def ver_mantenimiento(mantenimiento_id):

    mantenimiento = obtener_mantenimiento_por_id(mantenimiento_id)

    if mantenimiento is None:
        abort(404)

    usuario_id_propietario = _usuario_id_propietario_actual()
    if usuario_id_propietario is not None and not propietario_tiene_acceso_mantenimiento(mantenimiento_id, usuario_id_propietario):
        abort(403)

    return render_template(
        "nueva_solicitud.html",
        form=mantenimiento,
        modo="ver",
        propiedades=[],
        proveedores=[],
    )


@mantenimientos_bp.route("/mantenimientos/<int:mantenimiento_id>/editar", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def editar_mantenimiento(mantenimiento_id):

    mantenimiento = obtener_mantenimiento_por_id(mantenimiento_id)

    if mantenimiento is None:
        abort(404)

    propiedades = obtener_propiedades_para_select()
    proveedores = obtener_proveedores_para_select()

    if request.method == "POST":

        datos = _leer_formulario()

        ok, error = actualizar_mantenimiento(mantenimiento_id, **datos)

        if error:
            return render_template(
                "nueva_solicitud.html",
                form=request.form,
                modo="editar",
                mantenimiento_id=mantenimiento_id,
                error=error,
                propiedades=propiedades,
                proveedores=proveedores,
            )

        return redirect(url_for("mantenimientos.mantenimientos"))

    return render_template(
        "nueva_solicitud.html",
        form=mantenimiento,
        modo="editar",
        mantenimiento_id=mantenimiento_id,
        propiedades=propiedades,
        proveedores=proveedores,
    )
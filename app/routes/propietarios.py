from flask import Blueprint, render_template, request, redirect, url_for, flash

from sqlalchemy import or_

from werkzeug.security import generate_password_hash

from app import db

from app.models.propietario import Propietario
from app.models.usuario import Usuario

from app.security import roles_required


propietarios_bp = Blueprint(
    "propietarios",
    __name__,
    url_prefix="/propietarios"
)


# =========================================================
# LISTAR PROPIETARIOS
# =========================================================

@propietarios_bp.route("/")
@roles_required("ADMINISTRADOR", "GESTOR")
def lista():

    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "todos")

    query = Propietario.query

    # -------------------------
    # BÚSQUEDA
    # -------------------------

    if buscar:

        patron = f"%{buscar}%"

        query = query.filter(
            or_(
                Propietario.nombre.ilike(patron),
                Propietario.apellido.ilike(patron),
                Propietario.dui.ilike(patron),
                Propietario.correo.ilike(patron)
            )
        )

    propietarios = query.order_by(
        Propietario.apellido,
        Propietario.nombre
    ).all()

    # -------------------------
    # FILTRO DE ESTADO
    # -------------------------

    if estado == "activo":

        propietarios = [
            propietario
            for propietario in propietarios
            if propietario.usuario is not None
            and propietario.usuario.activo
        ]

    elif estado == "inactivo":

        propietarios = [
            propietario
            for propietario in propietarios
            if propietario.usuario is not None
            and not propietario.usuario.activo
        ]

    return render_template(
        "propietarios.html",
        propietarios=propietarios,
        buscar=buscar,
        estado=estado
    )


# =========================================================
# VER PROPIETARIO
# =========================================================

@propietarios_bp.route("/<int:propietario_id>")
@roles_required("ADMINISTRADOR", "GESTOR")
def detalle(propietario_id):

    propietario = db.session.get(
        Propietario,
        propietario_id
    )

    if propietario is None:
        return "Propietario no encontrado.", 404

    return render_template(
        "nuevo_propietario.html",
        propietario=propietario,
        modo="detalle"  
    )


# =========================================================
# NUEVO PROPIETARIO
# =========================================================

@propietarios_bp.route("/nuevo", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        dui = request.form.get("dui", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        username = request.form.get("usuario", "").strip()
        password = request.form.get("contrasena", "")

        # Validaciones
        if not nombre or not apellido or not dui:
            flash("Nombre, apellido y DUI son obligatorios.", "danger")
            return render_template(
                "nuevo_propietario.html",
                propietario=None,
                form=request.form
            )

        if not username or not password:
            flash(
                "El nombre de usuario y la contraseña son obligatorios.",
                "danger"
            )
            return render_template(
                "nuevo_propietario.html",
                propietario=None,
                form=request.form
            )

        # DUI duplicado
        if Propietario.query.filter_by(dui=dui).first():
            flash("Ya existe un propietario con ese DUI.", "danger")
            return render_template(
                "nuevo_propietario.html",
                propietario=None,
                form=request.form
            )

        # Usuario duplicado
        if Usuario.query.filter_by(username=username).first():
            flash("Ese nombre de usuario ya existe.", "danger")
            return render_template(
                "nuevo_propietario.html",
                propietario=None,
                form=request.form
            )

        # Crear usuario
        usuario = Usuario(
            username=username,
            password_hash=generate_password_hash(password),
            rol="PROPIETARIO",
            activo=True
        )

        # Crear propietario
        propietario = Propietario(
            nombre=nombre,
            apellido=apellido,
            dui=dui,
            telefono=telefono or None,
            correo=correo or None,
            usuario=usuario
        )

        db.session.add(usuario)
        db.session.add(propietario)

        try:
            db.session.commit()

            flash(
                "Propietario registrado correctamente.",
                "success"
            )

            return redirect(url_for("propietarios.lista"))

        except Exception:
            db.session.rollback()

            flash(
                "Ocurrió un error al registrar el propietario.",
                "danger"
            )

            return render_template(
                "nuevo_propietario.html",
                propietario=None,
                form=request.form
            )

    return render_template(
        "nuevo_propietario.html",
        propietario=None,
        form=None
    )


# =========================================================
# EDITAR PROPIETARIO
# =========================================================

@propietarios_bp.route(
    "/<int:propietario_id>/editar",
    methods=["GET", "POST"]
)
@roles_required("ADMINISTRADOR", "GESTOR")
def editar(propietario_id):

    propietario = db.session.get(
        Propietario,
        propietario_id
    )

    if propietario is None:

        return "Propietario no encontrado.", 404


    # =====================================================
    # GET
    # =====================================================

    if request.method == "GET":

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


    # =====================================================
    # POST
    # =====================================================

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    apellido = request.form.get(
        "apellido",
        ""
    ).strip()

    dui = request.form.get(
        "dui",
        ""
    ).strip()

    telefono = request.form.get(
        "telefono",
        ""
    ).strip()

    correo = request.form.get(
        "correo",
        ""
    ).strip()

    username = request.form.get(
        "usuario",
        ""
    ).strip()

    password = request.form.get(
        "contrasena",
        ""
    )


    # ---------------------------------
    # VALIDACIONES
    # ---------------------------------

    if not nombre or not apellido or not dui:

        flash(
            "Nombre, apellido y DUI son obligatorios.",
            "danger"
        )

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


    if not username:

        flash(
            "El nombre de usuario es obligatorio.",
            "danger"
        )

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


    # ---------------------------------
    # VERIFICAR DUI
    # ---------------------------------

    existente = Propietario.query.filter(
        Propietario.dui == dui,
        Propietario.id != propietario.id
    ).first()

    if existente:

        flash(
            "Otro propietario ya utiliza ese DUI.",
            "danger"
        )

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


    # ---------------------------------
    # VERIFICAR USERNAME
    # ---------------------------------

    usuario_existente = Usuario.query.filter(
        Usuario.username == username,
        Usuario.id != (
            propietario.usuario.id
            if propietario.usuario
            else -1
        )
    ).first()

    if usuario_existente:

        flash(
            "Ese nombre de usuario ya existe.",
            "danger"
        )

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


    # ---------------------------------
    # ACTUALIZAR PROPIETARIO
    # ---------------------------------

    propietario.nombre = nombre
    propietario.apellido = apellido
    propietario.dui = dui
    propietario.telefono = telefono or None
    propietario.correo = correo or None


    # ---------------------------------
    # ACTUALIZAR CUENTA
    # ---------------------------------

    if propietario.usuario is None:

        # Esto sería solo una protección por si
        # existe algún propietario antiguo sin usuario.

        usuario = Usuario(
            username=username,
            password_hash=generate_password_hash(password),
            rol="PROPIETARIO",
            activo=True
        )

        propietario.usuario = usuario

        db.session.add(usuario)

    else:

        propietario.usuario.username = username

        # La contraseña solo cambia si se escribió una nueva.
        if password:

            propietario.usuario.password_hash = (
                generate_password_hash(password)
            )


    # ---------------------------------
    # GUARDAR
    # ---------------------------------

    try:

        db.session.commit()

        flash(
            "Propietario y cuenta actualizados correctamente.",
            "success"
        )

        return redirect(
            url_for("propietarios.lista")
        )

    except Exception:

        db.session.rollback()

        flash(
            "Ocurrió un error al actualizar el propietario.",
            "danger"
        )

        return render_template(
            "nuevo_propietario.html",
            propietario=propietario
        )


# =========================================================
# ACTIVAR / DESACTIVAR CUENTA
# =========================================================

@propietarios_bp.route(
    "/<int:propietario_id>/estado",
    methods=["POST"]
)
@roles_required("ADMINISTRADOR")
def cambiar_estado(propietario_id):

    propietario = db.session.get(
        Propietario,
        propietario_id
    )

    if propietario is None:

        return "Propietario no encontrado.", 404


    if propietario.usuario is None:

        flash(
            "El propietario no tiene una cuenta de usuario.",
            "warning"
        )

        return redirect(
            url_for("propietarios.lista")
        )


    propietario.usuario.activo = (
        not propietario.usuario.activo
    )

    db.session.commit()


    if propietario.usuario.activo:

        flash(
            "La cuenta del propietario fue activada.",
            "success"
        )

    else:

        flash(
            "La cuenta del propietario fue desactivada.",
            "warning"
        )


    return redirect(
        url_for("propietarios.lista")
    )
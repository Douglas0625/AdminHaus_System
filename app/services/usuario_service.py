import re

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import db
from app.models.usuario import Usuario
from app.models.propietario import Propietario


ROLES_ASIGNABLES = ("GESTOR", "PROPIETARIO")
ESTADOS_VALIDOS = ("activo", "inactivo")

_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# =========================================================
# LISTADO / BÚSQUEDA
# =========================================================

def obtener_usuarios(buscar="", rol="todos", estado="todos"):
    """
    Usuarios del sistema, con búsqueda por username y filtros
    por rol/estado. La lógica de consulta vive aquí, no en la
    ruta ni en el template.
    """

    query = Usuario.query

    buscar = (buscar or "").strip()

    if buscar:
        query = query.filter(Usuario.username.ilike(f"%{buscar}%"))

    if rol and rol != "todos" and rol in ("ADMINISTRADOR", "GESTOR", "PROPIETARIO"):
        query = query.filter(Usuario.rol == rol)

    if estado == "activo":
        query = query.filter(Usuario.activo.is_(True))
    elif estado == "inactivo":
        query = query.filter(Usuario.activo.is_(False))

    return query.order_by(Usuario.username).all()


def obtener_usuario(usuario_id):
    return db.session.get(Usuario, usuario_id)


def obtener_propietarios_disponibles():
    """
    Propietarios sin cuenta de usuario todavía (usuario_id IS NULL).
    Se usan para 'vincular' un propietario existente a un usuario
    PROPIETARIO nuevo, en lugar de crear uno desde cero.
    """

    return Propietario.query.filter(
        Propietario.usuario_id.is_(None)
    ).order_by(
        Propietario.apellido,
        Propietario.nombre,
    ).all()


# =========================================================
# VALIDACIONES COMUNES
# =========================================================

def _validar_username(username, usuario_id_excluir=None):

    errores = []

    if not username:
        errores.append("El nombre de usuario es obligatorio.")
        return errores

    if len(username) > 50:
        errores.append("El nombre de usuario no puede superar los 50 caracteres.")

    query = Usuario.query.filter(Usuario.username == username)

    if usuario_id_excluir is not None:
        query = query.filter(Usuario.id != usuario_id_excluir)

    if query.first() is not None:
        errores.append("Ese nombre de usuario ya existe.")

    return errores


def _validar_datos_propietario_nuevo(nombre, apellido, dui, correo, propietario_id_excluir=None):

    errores = []

    if not nombre:
        errores.append("El nombre del propietario es obligatorio.")

    if not apellido:
        errores.append("El apellido del propietario es obligatorio.")

    if not dui:
        errores.append("El DUI del propietario es obligatorio.")
    else:
        query = Propietario.query.filter(Propietario.dui == dui)

        if propietario_id_excluir is not None:
            query = query.filter(Propietario.id != propietario_id_excluir)

        if query.first() is not None:
            errores.append("Ya existe un propietario con ese DUI.")

    if correo and not _PATRON_CORREO.match(correo):
        errores.append("El correo electrónico no tiene un formato válido.")

    return errores


def _leer_datos_propietario_form(datos, prefijo="propietario_"):
    return {
        "nombre": (datos.get(f"{prefijo}nombre") or "").strip(),
        "apellido": (datos.get(f"{prefijo}apellido") or "").strip(),
        "dui": (datos.get(f"{prefijo}dui") or "").strip(),
        "telefono": (datos.get(f"{prefijo}telefono") or "").strip(),
        "correo": (datos.get(f"{prefijo}correo") or "").strip(),
    }


def _resolver_propietario_nuevo_usuario(datos, errores, propietario_id_excluir=None):
    """
    Resuelve el sub-modo 'existente' / 'nuevo' del bloque de
    Propietario cuando un usuario PROPIETARIO todavía no tiene
    un Propietario vinculado (creación, o edición de un caso
    huérfano). Devuelve (propietario_a_vincular, datos_nuevo).
    Agrega los errores encontrados a la lista 'errores' recibida.
    """

    propietario_modo = datos.get("propietario_modo", "existente")

    if propietario_modo == "existente":

        propietario_id = (datos.get("propietario_id") or "").strip()

        if not propietario_id:
            errores.append("Selecciona el propietario que deseas vincular.")
            return None, None

        try:
            propietario = db.session.get(Propietario, int(propietario_id))
        except ValueError:
            propietario = None

        if propietario is None:
            errores.append("El propietario seleccionado no existe.")
        elif propietario.usuario_id is not None:
            errores.append("Ese propietario ya tiene una cuenta asociada.")
            propietario = None

        return propietario, None

    # propietario_modo == "nuevo"
    campos = _leer_datos_propietario_form(datos)

    errores += _validar_datos_propietario_nuevo(
        campos["nombre"], campos["apellido"], campos["dui"], campos["correo"],
        propietario_id_excluir=propietario_id_excluir,
    )

    if errores:
        return None, None

    campos["telefono"] = campos["telefono"] or None
    campos["correo"] = campos["correo"] or None

    return None, campos


# =========================================================
# CREAR USUARIO
# =========================================================

def crear_usuario(datos, admin_actual):
    """
    Crea un usuario nuevo (GESTOR o PROPIETARIO; no se permite
    crear otro ADMINISTRADOR desde este formulario). Si el rol
    es PROPIETARIO, además vincula un Propietario existente sin
    cuenta o crea uno nuevo, dentro de la misma transacción: si
    algo falla no queda ni el usuario ni el propietario a medias.
    """

    errores = []

    username = (datos.get("usuario") or "").strip()
    password = datos.get("contrasena") or ""
    confirmar = datos.get("confirmar_contrasena") or ""
    rol = (datos.get("rol") or "").strip().upper()
    estado = (datos.get("estado") or "activo").strip().lower()

    errores += _validar_username(username)

    if not password:
        errores.append("La contraseña es obligatoria.")
    elif password != confirmar:
        errores.append("Las contraseñas no coinciden.")

    if rol not in ROLES_ASIGNABLES:
        errores.append("El rol debe ser GESTOR o PROPIETARIO.")

    if estado not in ESTADOS_VALIDOS:
        estado = "activo"

    propietario_a_vincular = None
    datos_propietario_nuevo = None

    if rol == "PROPIETARIO":
        propietario_a_vincular, datos_propietario_nuevo = _resolver_propietario_nuevo_usuario(
            datos, errores,
        )

    if errores:
        return None, errores

    usuario = Usuario(
        username=username,
        password_hash=generate_password_hash(password),
        rol=rol,
        activo=(estado == "activo"),
    )

    db.session.add(usuario)

    if propietario_a_vincular is not None:
        propietario_a_vincular.usuario = usuario
    elif datos_propietario_nuevo is not None:
        db.session.add(Propietario(usuario=usuario, **datos_propietario_nuevo))

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, ["Ocurrió un error al guardar (usuario o DUI duplicado)."]

    return usuario, []


# =========================================================
# ACTUALIZAR USUARIO
# =========================================================

def actualizar_usuario(usuario, datos, admin_actual):
    """
    Actualiza usuario y, cuando corresponde, su Propietario
    relacionado. El rol de un ADMINISTRADOR nunca se modifica
    aquí. Si el usuario ya tiene un Propietario vinculado, sus
    datos se editan directamente; si es PROPIETARIO sin
    Propietario vinculado (caso huérfano), se resuelve igual
    que en la creación (vincular existente o crear nuevo).
    """

    errores = []

    username = (datos.get("usuario") or "").strip()
    password = datos.get("contrasena") or ""
    confirmar = datos.get("confirmar_contrasena") or ""
    estado = (datos.get("estado") or "activo").strip().lower()

    errores += _validar_username(username, usuario_id_excluir=usuario.id)

    if password and password != confirmar:
        errores.append("Las contraseñas no coinciden.")

    if estado not in ESTADOS_VALIDOS:
        estado = "activo"

    # Un administrador no puede bloquear su propia cuenta,
    # tampoco desde este formulario de edición.
    if (
        admin_actual is not None
        and usuario.id == admin_actual.id
        and estado == "inactivo"
    ):
        errores.append("No puedes bloquear tu propia cuenta.")

    rol_actual = usuario.rol

    if rol_actual == "ADMINISTRADOR":
        # El rol de una cuenta ADMINISTRADOR no se toca desde
        # este módulo (evita convertir/perder cuentas admin).
        rol_nuevo = "ADMINISTRADOR"
    else:
        rol_nuevo = (datos.get("rol") or rol_actual).strip().upper()

        if rol_nuevo not in ROLES_ASIGNABLES:
            errores.append("El rol debe ser GESTOR o PROPIETARIO.")
        elif (
            rol_actual == "PROPIETARIO"
            and rol_nuevo != "PROPIETARIO"
            and usuario.propietario is not None
        ):
            errores.append(
                "No se puede cambiar el rol: este usuario tiene un propietario asociado."
            )

    propietario_a_vincular = None
    datos_propietario_nuevo = None
    datos_propietario_actualizar = None

    if rol_nuevo == "PROPIETARIO" and not errores:

        if usuario.propietario is not None:

            campos = _leer_datos_propietario_form(datos)

            errores += _validar_datos_propietario_nuevo(
                campos["nombre"], campos["apellido"], campos["dui"], campos["correo"],
                propietario_id_excluir=usuario.propietario.id,
            )

            if not errores:
                campos["telefono"] = campos["telefono"] or None
                campos["correo"] = campos["correo"] or None
                datos_propietario_actualizar = campos

        else:
            propietario_a_vincular, datos_propietario_nuevo = _resolver_propietario_nuevo_usuario(
                datos, errores,
            )

    if errores:
        return False, errores

    usuario.username = username
    usuario.rol = rol_nuevo
    usuario.activo = (estado == "activo")

    if password:
        usuario.password_hash = generate_password_hash(password)

    if datos_propietario_actualizar is not None:
        for campo, valor in datos_propietario_actualizar.items():
            setattr(usuario.propietario, campo, valor)
    elif propietario_a_vincular is not None:
        propietario_a_vincular.usuario = usuario
    elif datos_propietario_nuevo is not None:
        db.session.add(Propietario(usuario=usuario, **datos_propietario_nuevo))

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False, ["Ocurrió un error al guardar (usuario o DUI duplicado)."]

    return True, []


# =========================================================
# BLOQUEAR / DESBLOQUEAR
# =========================================================

def cambiar_estado(usuario, admin_actual):
    """
    Alterna 'activo'. Un administrador no puede bloquear su
    propia cuenta (evitaría que se quede sin acceso al sistema).
    """

    if admin_actual is not None and usuario.id == admin_actual.id:
        return False, "No puedes bloquear tu propia cuenta."

    usuario.activo = not usuario.activo
    db.session.commit()

    return True, None

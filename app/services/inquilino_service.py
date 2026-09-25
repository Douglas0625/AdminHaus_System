from sqlalchemy import text

from app import db


def obtener_inquilinos(buscar="", estado="todos"):
    """
    Obtiene los inquilinos junto con la propiedad de su contrato
    ACTIVO (si tiene uno), para la pantalla de Inquilinos.
    """

    # -----------------------------
    # INQUILINOS + PROPIEDAD DEL CONTRATO ACTIVO
    # -----------------------------

    patron = f"%{buscar}%"

    filas_bd = db.session.execute(
        text("""
            SELECT
                inquilino.id,
                inquilino.nombre,
                inquilino.apellido,
                inquilino.dui,
                inquilino.telefono,
                inquilino.correo,
                propiedad.tipo AS propiedad_tipo,
                propiedad.codigo AS propiedad_codigo
            FROM inquilino
            LEFT JOIN contrato
                ON contrato.inquilino_id = inquilino.id
                AND contrato.estado = 'ACTIVO'
            LEFT JOIN propiedad
                ON propiedad.id = contrato.propiedad_id
            WHERE (
                :buscar = ''
                OR inquilino.nombre ILIKE :patron
                OR inquilino.apellido ILIKE :patron
                OR inquilino.dui ILIKE :patron
                OR inquilino.correo ILIKE :patron
            )
            ORDER BY inquilino.nombre, inquilino.apellido
        """),
        {
            "buscar": buscar,
            "patron": patron
        }
    ).mappings().all()

    # -----------------------------
    # CALCULAR ESTADO Y FILTRAR
    # -----------------------------
    # Un inquilino se considera "activo" si tiene contrato ACTIVO
    # (es decir, si le llegó una propiedad en el JOIN de arriba).

    filas = []

    for fila in filas_bd:

        activo = fila["propiedad_codigo"] is not None

        if estado == "activo" and not activo:
            continue

        if estado == "inactivo" and activo:
            continue

        propiedad_texto = None

        if activo:
            propiedad_texto = f"{fila['propiedad_tipo'].capitalize()} {fila['propiedad_codigo']}"

        filas.append({
            "id": fila["id"],
            "nombre": fila["nombre"],
            "apellido": fila["apellido"],
            "dui": fila["dui"],
            "telefono": fila["telefono"],
            "correo": fila["correo"],
            "propiedad_texto": propiedad_texto,
            "activo": activo,
        })

    return filas


def existe_dui(dui, excluir_id=None):
    """
    Verifica si ya existe un inquilino registrado con ese DUI.
    Si se pasa 'excluir_id', ignora ese inquilino en la búsqueda
    (para permitir guardar sin cambiar el propio DUI al editar).
    """

    parametros = {"dui": dui}
    condicion_extra = ""

    if excluir_id is not None:
        condicion_extra = "AND id <> :excluir_id"
        parametros["excluir_id"] = excluir_id

    resultado = db.session.execute(
        text(f"""
            SELECT id
            FROM inquilino
            WHERE dui = :dui
            {condicion_extra}
        """),
        parametros
    ).scalar_one_or_none()

    return resultado is not None


def crear_inquilino(nombre, apellido, dui, telefono, correo):
    """
    Crea un inquilino nuevo.
    Devuelve una tupla (inquilino_id, error):
    - Si error es None, el inquilino se guardó correctamente.
    - Si error trae un mensaje, no se guardó nada.
    """

    if not nombre or not apellido or not dui:
        return None, "Nombre, apellido y DUI son obligatorios."

    if existe_dui(dui):
        return None, "Ya existe un inquilino registrado con ese DUI."

    nuevo_id = db.session.execute(
        text("""
            INSERT INTO inquilino (nombre, apellido, dui, telefono, correo)
            VALUES (:nombre, :apellido, :dui, :telefono, :correo)
            RETURNING id
        """),
        {
            "nombre": nombre,
            "apellido": apellido,
            "dui": dui,
            "telefono": telefono or None,
            "correo": correo or None,
        }
    ).scalar_one()

    db.session.commit()

    return nuevo_id, None

def obtener_inquilino_por_id(inquilino_id):
    """
    Obtiene un inquilino por su id, junto con la propiedad de su
    contrato ACTIVO (si tiene uno). Devuelve None si no existe.
    """

    fila = db.session.execute(
        text("""
            SELECT
                inquilino.id,
                inquilino.nombre,
                inquilino.apellido,
                inquilino.dui,
                inquilino.telefono,
                inquilino.correo,
                propiedad.tipo AS propiedad_tipo,
                propiedad.codigo AS propiedad_codigo
            FROM inquilino
            LEFT JOIN contrato
                ON contrato.inquilino_id = inquilino.id
                AND contrato.estado = 'ACTIVO'
            LEFT JOIN propiedad
                ON propiedad.id = contrato.propiedad_id
            WHERE inquilino.id = :inquilino_id
        """),
        {
            "inquilino_id": inquilino_id
        }
    ).mappings().first()

    if fila is None:
        return None

    activo = fila["propiedad_codigo"] is not None

    propiedad_texto = None

    if activo:
        propiedad_texto = f"{fila['propiedad_tipo'].capitalize()} {fila['propiedad_codigo']}"

    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "apellido": fila["apellido"],
        "dui": fila["dui"],
        "telefono": fila["telefono"],
        "correo": fila["correo"],
        "propiedad_texto": propiedad_texto,
        "activo": activo,
    }


def actualizar_inquilino(inquilino_id, nombre, apellido, dui, telefono, correo):
    """
    Actualiza los datos de un inquilino existente.
    Devuelve una tupla (ok, error):
    - Si error es None, se actualizó correctamente (ok = True).
    - Si error trae un mensaje, no se guardó nada (ok = False).
    """

    if not nombre or not apellido or not dui:
        return False, "Nombre, apellido y DUI son obligatorios."

    if existe_dui(dui, excluir_id=inquilino_id):
        return False, "Ya existe otro inquilino registrado con ese DUI."

    resultado = db.session.execute(
        text("""
            UPDATE inquilino
            SET nombre = :nombre,
                apellido = :apellido,
                dui = :dui,
                telefono = :telefono,
                correo = :correo
            WHERE id = :inquilino_id
        """),
        {
            "nombre": nombre,
            "apellido": apellido,
            "dui": dui,
            "telefono": telefono or None,
            "correo": correo or None,
            "inquilino_id": inquilino_id,
        }
    )

    db.session.commit()

    if resultado.rowcount == 0:
        return False, "No se encontró el inquilino a actualizar."

    return True, None
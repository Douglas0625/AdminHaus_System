from sqlalchemy import text

from app import db


def obtener_mantenimientos(buscar="", estado="todos"):
    """
    Obtiene las solicitudes de mantenimiento junto con el código
    de la propiedad y el nombre del proveedor (si tiene uno).
    """

    patron = f"%{buscar}%"

    mapa_estado = {
        "pendiente": "PENDIENTE",
        "en-proceso": "EN PROCESO",
        "resuelto": "RESUELTO",
        "cancelado": "CANCELADO",
    }
    estado_bd = mapa_estado.get(estado)

    filas = db.session.execute(
        text("""
            SELECT
                mantenimiento.id,
                mantenimiento.categoria,
                mantenimiento.descripcion,
                mantenimiento.fecha_solicitud,
                mantenimiento.estado,
                mantenimiento.costo,
                propiedad.codigo AS propiedad_codigo,
                propiedad.tipo AS propiedad_tipo,
                proveedor_mantenimiento.nombre AS proveedor_nombre
            FROM mantenimiento
            INNER JOIN propiedad
                ON mantenimiento.propiedad_id = propiedad.id
            LEFT JOIN proveedor_mantenimiento
                ON mantenimiento.proveedor_id = proveedor_mantenimiento.id
            WHERE (
                :buscar = ''
                OR propiedad.codigo ILIKE :patron
                OR mantenimiento.descripcion ILIKE :patron
            )
            AND (
                CAST(:estado_bd AS text) IS NULL
                OR mantenimiento.estado = CAST(:estado_bd AS text)
            )
            ORDER BY mantenimiento.fecha_solicitud DESC, mantenimiento.id DESC
        """),
        {
            "buscar": buscar,
            "patron": patron,
            "estado_bd": estado_bd,
        }
    ).mappings().all()

    filas_resultado = []

    for fila in filas:
        filas_resultado.append({
            "id": fila["id"],
            "propiedad_texto": f"{fila['propiedad_tipo'].capitalize()} {fila['propiedad_codigo']}",
            "categoria": fila["categoria"],
            "descripcion": fila["descripcion"],
            "proveedor_texto": fila["proveedor_nombre"] or "Sin proveedor",
            "fecha_solicitud": fila["fecha_solicitud"],
            "estado": fila["estado"],
            "costo": fila["costo"] or 0,
        })

    return filas_resultado


def obtener_propiedades_para_select():
    """
    Todas las propiedades, para llenar el <select> del formulario.
    """

    return db.session.execute(
        text("""
            SELECT id, codigo, tipo
            FROM propiedad
            ORDER BY codigo
        """)
    ).mappings().all()


def obtener_proveedores_para_select():
    """
    Todos los proveedores de mantenimiento, para llenar el <select>.
    """

    return db.session.execute(
        text("""
            SELECT id, nombre, tipo
            FROM proveedor_mantenimiento
            ORDER BY nombre
        """)
    ).mappings().all()


def obtener_mantenimiento_por_id(mantenimiento_id):
    """
    Obtiene una solicitud de mantenimiento con los datos de su
    propiedad y proveedor. Devuelve None si no existe.
    """

    fila = db.session.execute(
        text("""
            SELECT
                mantenimiento.id,
                mantenimiento.propiedad_id,
                mantenimiento.proveedor_id,
                mantenimiento.categoria,
                mantenimiento.descripcion,
                mantenimiento.fecha_solicitud,
                mantenimiento.estado,
                mantenimiento.costo,
                mantenimiento.observaciones,
                propiedad.codigo AS propiedad_codigo,
                propiedad.tipo AS propiedad_tipo,
                proveedor_mantenimiento.nombre AS proveedor_nombre
            FROM mantenimiento
            INNER JOIN propiedad
                ON mantenimiento.propiedad_id = propiedad.id
            LEFT JOIN proveedor_mantenimiento
                ON mantenimiento.proveedor_id = proveedor_mantenimiento.id
            WHERE mantenimiento.id = :mantenimiento_id
        """),
        {
            "mantenimiento_id": mantenimiento_id
        }
    ).mappings().first()

    if fila is None:
        return None

    return {
        "id": fila["id"],
        "propiedad_id": fila["propiedad_id"],
        "proveedor_id": fila["proveedor_id"],
        "categoria": fila["categoria"],
        "descripcion": fila["descripcion"],
        "fecha_solicitud": fila["fecha_solicitud"].isoformat(),
        "estado": fila["estado"],
        "costo": fila["costo"],
        "observaciones": fila["observaciones"],
        "propiedad_texto": f"{fila['propiedad_tipo'].capitalize()} {fila['propiedad_codigo']}",
        "proveedor_texto": fila["proveedor_nombre"] or "Sin proveedor",
    }


def _validar_datos_mantenimiento(propiedad_id, categoria, descripcion, fecha_solicitud, estado, costo):

    if not propiedad_id or not categoria or not descripcion or not fecha_solicitud or not estado:
        return "Propiedad, categoría, descripción, fecha de solicitud y estado son obligatorios."

    if estado not in ("PENDIENTE", "EN PROCESO", "RESUELTO", "CANCELADO"):
        return "El estado no es válido."

    if costo:
        try:
            if float(costo) < 0:
                return "El costo no puede ser negativo."
        except ValueError:
            return "El costo no es un número válido."

    return None


def crear_mantenimiento(propiedad_id, proveedor_id, categoria, descripcion, fecha_solicitud, estado, costo, observaciones):
    """
    Crea una solicitud de mantenimiento nueva.
    Devuelve una tupla (mantenimiento_id, error).
    """

    error = _validar_datos_mantenimiento(
        propiedad_id, categoria, descripcion, fecha_solicitud, estado, costo
    )

    if error:
        return None, error

    nuevo_id = db.session.execute(
        text("""
            INSERT INTO mantenimiento (
                propiedad_id, proveedor_id, categoria, descripcion,
                fecha_solicitud, estado, costo, observaciones
            )
            VALUES (
                :propiedad_id, :proveedor_id, :categoria, :descripcion,
                :fecha_solicitud, :estado, :costo, :observaciones
            )
            RETURNING id
        """),
        {
            "propiedad_id": propiedad_id,
            "proveedor_id": proveedor_id or None,
            "categoria": categoria,
            "descripcion": descripcion,
            "fecha_solicitud": fecha_solicitud,
            "estado": estado,
            "costo": costo or None,
            "observaciones": observaciones or None,
        }
    ).scalar_one()

    db.session.commit()

    return nuevo_id, None


def actualizar_mantenimiento(mantenimiento_id, propiedad_id, proveedor_id, categoria, descripcion, fecha_solicitud, estado, costo, observaciones):
    """
    Actualiza una solicitud de mantenimiento existente.
    Devuelve una tupla (ok, error).
    """

    error = _validar_datos_mantenimiento(
        propiedad_id, categoria, descripcion, fecha_solicitud, estado, costo
    )

    if error:
        return False, error

    resultado = db.session.execute(
        text("""
            UPDATE mantenimiento
            SET propiedad_id = :propiedad_id,
                proveedor_id = :proveedor_id,
                categoria = :categoria,
                descripcion = :descripcion,
                fecha_solicitud = :fecha_solicitud,
                estado = :estado,
                costo = :costo,
                observaciones = :observaciones
            WHERE id = :mantenimiento_id
        """),
        {
            "propiedad_id": propiedad_id,
            "proveedor_id": proveedor_id or None,
            "categoria": categoria,
            "descripcion": descripcion,
            "fecha_solicitud": fecha_solicitud,
            "estado": estado,
            "costo": costo or None,
            "observaciones": observaciones or None,
            "mantenimiento_id": mantenimiento_id,
        }
    )

    db.session.commit()

    if resultado.rowcount == 0:
        return False, "No se encontró la solicitud a actualizar."

    return True, None
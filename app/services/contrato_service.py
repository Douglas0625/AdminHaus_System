from sqlalchemy import text

from app import db


def obtener_contratos(buscar="", estado="todos"):
    """
    Obtiene los contratos junto con el código de la propiedad
    y el nombre del inquilino, para la pantalla de Contratos.
    """

    patron = f"%{buscar}%"

    # 'todos' en la UI no filtra; los demás valores se traducen
    # al estado real que se guarda en la base de datos.
    mapa_estado = {
        "vigente": "ACTIVO",
        "finalizado": "FINALIZADO",
        "cancelado": "CANCELADO",
    }
    estado_bd = mapa_estado.get(estado)

    filas = db.session.execute(
        text("""
            SELECT
                contrato.id,
                contrato.fecha_inicio,
                contrato.fecha_fin,
                contrato.monto_mensual,
                contrato.estado,
                propiedad.codigo AS propiedad_codigo,
                inquilino.nombre AS inquilino_nombre,
                inquilino.apellido AS inquilino_apellido
            FROM contrato
            INNER JOIN propiedad
                ON contrato.propiedad_id = propiedad.id
            INNER JOIN inquilino
                ON contrato.inquilino_id = inquilino.id
            WHERE (
                :buscar = ''
                OR propiedad.codigo ILIKE :patron
                OR inquilino.nombre ILIKE :patron
                OR inquilino.apellido ILIKE :patron
            )
            AND (
                CAST(:estado_bd AS text) IS NULL
                OR contrato.estado = CAST(:estado_bd AS text)
            )
            ORDER BY contrato.id
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
            "codigo": f"CT-{fila['id']:03d}",
            "propiedad_codigo": fila["propiedad_codigo"],
            "inquilino_texto": f"{fila['inquilino_nombre']} {fila['inquilino_apellido']}",
            "fecha_inicio": fila["fecha_inicio"],
            "fecha_fin": fila["fecha_fin"],
            "monto_mensual": fila["monto_mensual"],
            "estado": fila["estado"],
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


def obtener_inquilinos_para_select():
    """
    Todos los inquilinos, para llenar el <select> del formulario.
    """

    return db.session.execute(
        text("""
            SELECT id, nombre, apellido
            FROM inquilino
            ORDER BY nombre, apellido
        """)
    ).mappings().all()


def obtener_contrato_por_id(contrato_id):
    """
    Obtiene un contrato con los datos de su propiedad e inquilino.
    Devuelve None si no existe.
    """

    fila = db.session.execute(
        text("""
            SELECT
                contrato.id,
                contrato.propiedad_id,
                contrato.inquilino_id,
                contrato.fecha_inicio,
                contrato.fecha_fin,
                contrato.monto_mensual,
                contrato.deposito,
                contrato.dia_pago,
                contrato.estado,
                propiedad.codigo AS propiedad_codigo,
                propiedad.tipo AS propiedad_tipo,
                inquilino.nombre AS inquilino_nombre,
                inquilino.apellido AS inquilino_apellido
            FROM contrato
            INNER JOIN propiedad ON contrato.propiedad_id = propiedad.id
            INNER JOIN inquilino ON contrato.inquilino_id = inquilino.id
            WHERE contrato.id = :contrato_id
        """),
        {
            "contrato_id": contrato_id
        }
    ).mappings().first()

    if fila is None:
        return None

    return {
        "id": fila["id"],
        "codigo": f"CT-{fila['id']:03d}",
        "propiedad_id": fila["propiedad_id"],
        "inquilino_id": fila["inquilino_id"],
        # Se guardan como texto (YYYY-MM-DD) para que <input type="date">
        # las entienda igual sea que vengan de la BD o de un formulario reenviado.
        "fecha_inicio": fila["fecha_inicio"].isoformat(),
        "fecha_fin": fila["fecha_fin"].isoformat(),
        "monto_mensual": fila["monto_mensual"],
        "deposito": fila["deposito"],
        "dia_pago": fila["dia_pago"],
        "estado": fila["estado"],
        "propiedad_texto": f"{fila['propiedad_tipo'].capitalize()} {fila['propiedad_codigo']}",
        "inquilino_texto": f"{fila['inquilino_nombre']} {fila['inquilino_apellido']}",
    }


def existe_contrato_activo(propiedad_id, excluir_id=None):
    """
    Revisa si una propiedad ya tiene un contrato en estado ACTIVO
    (regla: una propiedad no puede tener más de un contrato activo).
    """

    parametros = {"propiedad_id": propiedad_id}
    condicion_extra = ""

    if excluir_id is not None:
        condicion_extra = "AND id <> :excluir_id"
        parametros["excluir_id"] = excluir_id

    resultado = db.session.execute(
        text(f"""
            SELECT id
            FROM contrato
            WHERE propiedad_id = :propiedad_id
              AND estado = 'ACTIVO'
              {condicion_extra}
        """),
        parametros
    ).scalar_one_or_none()

    return resultado is not None


def _validar_datos_contrato(propiedad_id, inquilino_id, fecha_inicio, fecha_fin, monto_mensual, dia_pago):

    if not propiedad_id or not inquilino_id or not fecha_inicio or not fecha_fin or not monto_mensual or not dia_pago:
        return "Propiedad, inquilino, fechas, monto mensual y día de pago son obligatorios."

    if fecha_fin < fecha_inicio:
        return "La fecha de fin no puede ser anterior a la fecha de inicio."

    try:
        if float(monto_mensual) < 0:
            return "El monto mensual no puede ser negativo."
    except ValueError:
        return "El monto mensual no es un número válido."

    try:
        if not (1 <= int(dia_pago) <= 31):
            return "El día de pago debe estar entre 1 y 31."
    except ValueError:
        return "El día de pago no es un número válido."

    return None


def crear_contrato(propiedad_id, inquilino_id, fecha_inicio, fecha_fin, monto_mensual, deposito, dia_pago):
    """
    Crea un contrato nuevo con estado ACTIVO.
    Devuelve una tupla (contrato_id, error).
    """

    error = _validar_datos_contrato(
        propiedad_id, inquilino_id, fecha_inicio, fecha_fin, monto_mensual, dia_pago
    )

    if error:
        return None, error

    if existe_contrato_activo(propiedad_id):
        return None, "Esa propiedad ya tiene un contrato ACTIVO. Finaliza o cancela el actual antes de crear uno nuevo."

    nuevo_id = db.session.execute(
        text("""
            INSERT INTO contrato (
                propiedad_id, inquilino_id, fecha_inicio, fecha_fin,
                monto_mensual, deposito, dia_pago, estado
            )
            VALUES (
                :propiedad_id, :inquilino_id, :fecha_inicio, :fecha_fin,
                :monto_mensual, :deposito, :dia_pago, 'ACTIVO'
            )
            RETURNING id
        """),
        {
            "propiedad_id": propiedad_id,
            "inquilino_id": inquilino_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "monto_mensual": monto_mensual,
            "deposito": deposito or 0,
            "dia_pago": dia_pago,
        }
    ).scalar_one()

    db.session.commit()

    return nuevo_id, None


def actualizar_contrato(contrato_id, propiedad_id, inquilino_id, fecha_inicio, fecha_fin, monto_mensual, deposito, dia_pago, estado):
    """
    Actualiza un contrato existente, incluyendo su estado
    (ACTIVO / FINALIZADO / CANCELADO).
    Devuelve una tupla (ok, error).
    """

    error = _validar_datos_contrato(
        propiedad_id, inquilino_id, fecha_inicio, fecha_fin, monto_mensual, dia_pago
    )

    if error:
        return False, error

    if estado not in ("ACTIVO", "FINALIZADO", "CANCELADO"):
        return False, "El estado del contrato no es válido."

    if estado == "ACTIVO" and existe_contrato_activo(propiedad_id, excluir_id=contrato_id):
        return False, "Esa propiedad ya tiene otro contrato ACTIVO."

    resultado = db.session.execute(
        text("""
            UPDATE contrato
            SET propiedad_id = :propiedad_id,
                inquilino_id = :inquilino_id,
                fecha_inicio = :fecha_inicio,
                fecha_fin = :fecha_fin,
                monto_mensual = :monto_mensual,
                deposito = :deposito,
                dia_pago = :dia_pago,
                estado = :estado
            WHERE id = :contrato_id
        """),
        {
            "propiedad_id": propiedad_id,
            "inquilino_id": inquilino_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "monto_mensual": monto_mensual,
            "deposito": deposito or 0,
            "dia_pago": dia_pago,
            "estado": estado,
            "contrato_id": contrato_id,
        }
    )

    db.session.commit()

    if resultado.rowcount == 0:
        return False, "No se encontró el contrato a actualizar."

    return True, None
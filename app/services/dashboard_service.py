from sqlalchemy import text

from app import db


def get_staff_dashboard():
    """
    Obtiene los datos generales utilizados por
    los dashboards del administrador y gestor.
    """

    # -----------------------------
    # PROPIEDADES
    # -----------------------------

    total_propiedades = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM propiedad
        """)
    ).scalar_one()

    propiedades_alquiladas = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM propiedad
            WHERE estado = 'ALQUILADA'
        """)
    ).scalar_one()

    # -----------------------------
    # PAGOS PENDIENTES
    # -----------------------------

    pagos_pendientes = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM pago
            WHERE estado = 'PENDIENTE'
        """)
    ).scalar_one()

    # -----------------------------
    # MANTENIMIENTOS ABIERTOS
    # -----------------------------

    mantenimientos_abiertos = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM mantenimiento
            WHERE estado IN ('PENDIENTE', 'EN PROCESO')
        """)
    ).scalar_one()

    # -----------------------------
    # PORCENTAJE DE PROPIEDADES
    # -----------------------------

    porcentaje_alquiladas = 0

    if total_propiedades > 0:
        porcentaje_alquiladas = round(
            (propiedades_alquiladas / total_propiedades) * 100,
            1
        )

    # -----------------------------
    # PAGOS RECIENTES
    # -----------------------------

    pagos_recientes = db.session.execute(
        text("""
            SELECT
                pago.id,
                pago.fecha_pago,
                pago.monto,
                contrato.id AS contrato_id,
                propiedad.codigo AS propiedad_codigo
            FROM pago
            INNER JOIN contrato
                ON pago.contrato_id = contrato.id
            INNER JOIN propiedad
                ON contrato.propiedad_id = propiedad.id
            WHERE pago.estado = 'PAGADO'
              AND pago.fecha_pago IS NOT NULL
            ORDER BY pago.fecha_pago DESC
            LIMIT 4
        """)
    ).mappings().all()

    # -----------------------------
    # MANTENIMIENTOS RECIENTES
    # -----------------------------

    mantenimientos_recientes = db.session.execute(
        text("""
            SELECT
                mantenimiento.id,
                mantenimiento.descripcion,
                mantenimiento.fecha_solicitud,
                mantenimiento.estado,
                propiedad.codigo AS propiedad_codigo
            FROM mantenimiento
            INNER JOIN propiedad
                ON mantenimiento.propiedad_id = propiedad.id
            ORDER BY mantenimiento.fecha_solicitud DESC
            LIMIT 4
        """)
    ).mappings().all()

    return {
        "total_propiedades": total_propiedades,
        "propiedades_alquiladas": propiedades_alquiladas,
        "pagos_pendientes": pagos_pendientes,
        "mantenimientos_abiertos": mantenimientos_abiertos,
        "porcentaje_alquiladas": porcentaje_alquiladas,
        "pagos_recientes": pagos_recientes,
        "mantenimientos_recientes": mantenimientos_recientes,
    }

def get_owner_dashboard(usuario_id):
    """
    Obtiene los datos del dashboard del propietario
    correspondiente al usuario autenticado.
    """

    # -----------------------------
    # OBTENER PROPIETARIO
    # -----------------------------

    propietario_id = db.session.execute(
        text("""
            SELECT id
            FROM propietario
            WHERE usuario_id = :usuario_id
        """),
        {
            "usuario_id": usuario_id
        }
    ).scalar_one_or_none()

    if propietario_id is None:
        return None

    # -----------------------------
    # TOTAL DE PROPIEDADES
    # -----------------------------

    total_propiedades = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM propiedad
            WHERE propietario_id = :propietario_id
        """),
        {
            "propietario_id": propietario_id
        }
    ).scalar_one()

    # -----------------------------
    # PROPIEDADES ALQUILADAS
    # -----------------------------

    propiedades_alquiladas = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM propiedad
            WHERE propietario_id = :propietario_id
              AND estado = 'ALQUILADA'
        """),
        {
            "propietario_id": propietario_id
        }
    ).scalar_one()

    # -----------------------------
    # PAGOS PENDIENTES
    # -----------------------------

    pagos_pendientes = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM pago
            INNER JOIN contrato
                ON pago.contrato_id = contrato.id
            INNER JOIN propiedad
                ON contrato.propiedad_id = propiedad.id
            WHERE propiedad.propietario_id = :propietario_id
              AND pago.estado = 'PENDIENTE'
        """),
        {
            "propietario_id": propietario_id
        }
    ).scalar_one()

    # -----------------------------
    # MANTENIMIENTOS ABIERTOS
    # -----------------------------

    mantenimientos_abiertos = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM mantenimiento
            INNER JOIN propiedad
                ON mantenimiento.propiedad_id = propiedad.id
            WHERE propiedad.propietario_id = :propietario_id
              AND mantenimiento.estado IN ('PENDIENTE', 'EN PROCESO')
        """),
        {
            "propietario_id": propietario_id
        }
    ).scalar_one()

    # -----------------------------
    # PROPIEDADES
    # -----------------------------

    propiedades = db.session.execute(
        text("""
            SELECT
                propiedad.id,
                propiedad.codigo,
                propiedad.tipo,
                propiedad.municipio,
                propiedad.precio_alquiler,
                propiedad.estado
            FROM propiedad
            WHERE propiedad.propietario_id = :propietario_id
            ORDER BY propiedad.id
        """),
        {
            "propietario_id": propietario_id
        }
    ).mappings().all()

    # -----------------------------
    # PAGOS PRÓXIMOS
    # -----------------------------

    pagos_proximos = db.session.execute(
        text("""
            SELECT
                pago.id,
                pago.fecha_esperada,
                pago.monto,
                pago.estado,
                propiedad.codigo AS propiedad_codigo
            FROM pago
            INNER JOIN contrato
                ON pago.contrato_id = contrato.id
            INNER JOIN propiedad
                ON contrato.propiedad_id = propiedad.id
            WHERE propiedad.propietario_id = :propietario_id
              AND pago.estado IN ('PENDIENTE', 'VENCIDO')
            ORDER BY pago.fecha_esperada ASC
            LIMIT 5
        """),
        {
            "propietario_id": propietario_id
        }
    ).mappings().all()

    # -----------------------------
    # MANTENIMIENTOS
    # -----------------------------

    mantenimientos = db.session.execute(
        text("""
            SELECT
                mantenimiento.id,
                mantenimiento.descripcion,
                mantenimiento.fecha_solicitud,
                mantenimiento.estado,
                propiedad.codigo AS propiedad_codigo
            FROM mantenimiento
            INNER JOIN propiedad
                ON mantenimiento.propiedad_id = propiedad.id
            WHERE propiedad.propietario_id = :propietario_id
            ORDER BY mantenimiento.fecha_solicitud DESC
            LIMIT 5
        """),
        {
            "propietario_id": propietario_id
        }
    ).mappings().all()

    return {
        "total_propiedades": total_propiedades,
        "propiedades_alquiladas": propiedades_alquiladas,
        "pagos_pendientes": pagos_pendientes,
        "mantenimientos_abiertos": mantenimientos_abiertos,
        "propiedades": propiedades,
        "pagos_proximos": pagos_proximos,
        "mantenimientos": mantenimientos,
    }
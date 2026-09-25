from app import db


class Mantenimiento(db.Model):

    __tablename__ = "mantenimiento"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    propiedad_id = db.Column(
        db.Integer,
        db.ForeignKey("propiedad.id", ondelete="RESTRICT"),
        nullable=False
    )

    proveedor_id = db.Column(
        db.Integer,
        db.ForeignKey("proveedor_mantenimiento.id", ondelete="SET NULL")
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    categoria = db.Column(
        db.String(100),
        nullable=False
    )

    fecha_solicitud = db.Column(
        db.Date,
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="PENDIENTE"
    )

    costo = db.Column(
        db.Numeric(10, 2)
    )

    observaciones = db.Column(
        db.Text
    )

    fecha_resolucion = db.Column(
        db.Date
    )

    __table_args__ = (
        db.CheckConstraint(
            "estado IN ('PENDIENTE', 'EN PROCESO', 'RESUELTO', 'CANCELADO')",
            name="chk_mantenimiento_estado"
        ),
        db.CheckConstraint(
            "costo IS NULL OR costo >= 0",
            name="chk_mantenimiento_costo"
        ),
        db.CheckConstraint(
            "fecha_resolucion IS NULL OR fecha_resolucion >= fecha_solicitud",
            name="chk_mantenimiento_fechas"
        ),
    )
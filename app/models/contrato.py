from app import db


class Contrato(db.Model):

    __tablename__ = "contrato"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    propiedad_id = db.Column(
        db.Integer,
        db.ForeignKey("propiedad.id", ondelete="RESTRICT"),
        nullable=False
    )

    inquilino_id = db.Column(
        db.Integer,
        db.ForeignKey("inquilino.id", ondelete="RESTRICT"),
        nullable=False
    )

    fecha_inicio = db.Column(
        db.Date,
        nullable=False
    )

    fecha_fin = db.Column(
        db.Date,
        nullable=False
    )

    monto_mensual = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    deposito = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    dia_pago = db.Column(
        db.Integer,
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVO"
    )

    contrato_anterior_id = db.Column(
        db.Integer,
        db.ForeignKey("contrato.id", ondelete="RESTRICT")
    )

    __table_args__ = (
        db.CheckConstraint(
            "fecha_fin >= fecha_inicio",
            name="chk_contrato_fechas"
        ),
        db.CheckConstraint(
            "monto_mensual >= 0",
            name="chk_contrato_monto"
        ),
        db.CheckConstraint(
            "deposito >= 0",
            name="chk_contrato_deposito"
        ),
        db.CheckConstraint(
            "dia_pago BETWEEN 1 AND 31",
            name="chk_contrato_dia_pago"
        ),
        db.CheckConstraint(
            "estado IN ('ACTIVO', 'FINALIZADO', 'CANCELADO')",
            name="chk_contrato_estado"
        ),
        # Regla: una propiedad no puede tener más de un contrato ACTIVO
        db.Index(
            "uq_contrato_propiedad_activo",
            "propiedad_id",
            unique=True,
            postgresql_where=db.text("estado = 'ACTIVO'")
        ),
    )
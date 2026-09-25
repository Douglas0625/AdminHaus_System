from app import db


class Pago(db.Model):

    __tablename__ = "pago"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    contrato_id = db.Column(
        db.Integer,
        db.ForeignKey("contrato.id", ondelete="RESTRICT"),
        nullable=False
    )

    fecha_esperada = db.Column(
        db.Date,
        nullable=False
    )

    fecha_pago = db.Column(
        db.Date
    )

    monto = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="PENDIENTE"
    )

    metodo_pago = db.Column(
        db.String(30)
    )

    __table_args__ = (
        db.CheckConstraint(
            "monto >= 0",
            name="chk_pago_monto"
        ),
        db.CheckConstraint(
            "estado IN ('PENDIENTE', 'PAGADO', 'VENCIDO')",
            name="chk_pago_estado"
        ),
        db.CheckConstraint(
            "estado <> 'PAGADO' OR fecha_pago IS NOT NULL",
            name="chk_pago_pagado"
        ),
        db.CheckConstraint(
            "estado <> 'PAGADO' OR metodo_pago IS NOT NULL",
            name="chk_pago_metodo"
        ),
    )
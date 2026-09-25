from app import db


class ProveedorMantenimiento(db.Model):

    __tablename__ = "proveedor_mantenimiento"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    telefono = db.Column(
        db.String(20)
    )

    correo = db.Column(
        db.String(150)
    )

    especialidad = db.Column(
        db.String(100)
    )

    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ('TECNICO', 'EMPRESA')",
            name="chk_proveedor_tipo"
        ),
    )
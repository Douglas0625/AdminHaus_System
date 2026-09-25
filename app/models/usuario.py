from app import db


class Usuario(db.Model):

    __tablename__ = "usuario"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    rol = db.Column(
        db.String(20),
        nullable=False
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    __table_args__ = (
        db.CheckConstraint(
            "rol IN ('ADMINISTRADOR', 'GESTOR', 'PROPIETARIO')",
            name="chk_usuario_rol"
        ),
    )
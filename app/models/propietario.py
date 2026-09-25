from app import db


class Propietario(db.Model):
    __tablename__ = "propietario"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    apellido = db.Column(
        db.String(100),
        nullable=False
    )

    dui = db.Column(
        db.String(10),
        nullable=False,
        unique=True
    )

    telefono = db.Column(
        db.String(20)
    )

    correo = db.Column(
        db.String(150)
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="SET NULL"),
        unique=True
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref(
            "propietario",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<Propietario {self.nombre} {self.apellido}>"
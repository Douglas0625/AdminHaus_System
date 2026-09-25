from app import db


class Inquilino(db.Model):

    __tablename__ = "inquilino"

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
        unique=True,
        nullable=False
    )

    telefono = db.Column(
        db.String(20)
    )

    correo = db.Column(
        db.String(150)
    )
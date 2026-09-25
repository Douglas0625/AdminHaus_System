from app import db


class Fotografia(db.Model):

    __tablename__ = "fotografia"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    propiedad_id = db.Column(
        db.Integer,
        db.ForeignKey("propiedad.id", ondelete="CASCADE"),
        nullable=False
    )

    ruta = db.Column(
        db.String(500),
        nullable=False
    )
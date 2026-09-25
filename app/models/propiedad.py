from app import db


class Propiedad(db.Model):

    __tablename__ = "propiedad"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    codigo = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    direccion = db.Column(
        db.Text,
        nullable=False
    )

    municipio = db.Column(
        db.String(100),
        nullable=False
    )

    departamento = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.Text
    )

    habitaciones = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    banos = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    parqueos = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    metros_cuadrados = db.Column(
        db.Numeric(10, 2)
    )

    precio_alquiler = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="DISPONIBLE"
    )

    propietario_id = db.Column(
        db.Integer,
        db.ForeignKey("propietario.id", ondelete="RESTRICT"),
        nullable=False
    )

    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ('CASA', 'APARTAMENTO')",
            name="chk_propiedad_tipo"
        ),
        db.CheckConstraint(
            "estado IN ('DISPONIBLE', 'ALQUILADA', 'INACTIVA')",
            name="chk_propiedad_estado"
        ),
        db.CheckConstraint(
            "habitaciones >= 0",
            name="chk_propiedad_habitaciones"
        ),
        db.CheckConstraint(
            "banos >= 0",
            name="chk_propiedad_banos"
        ),
        db.CheckConstraint(
            "parqueos >= 0",
            name="chk_propiedad_parqueos"
        ),
        db.CheckConstraint(
            "metros_cuadrados IS NULL OR metros_cuadrados > 0",
            name="chk_propiedad_metros"
        ),
        db.CheckConstraint(
            "precio_alquiler >= 0",
            name="chk_propiedad_precio"
        ),
    )
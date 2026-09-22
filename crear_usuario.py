from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario


app = create_app()


with app.app_context():

    print("=== Crear administrador inicial ===")

    username = input("Usuario: ").strip()
    password = getpass("Contraseña: ")

    if not username or not password:
        print("El usuario y la contraseña son obligatorios.")
        raise SystemExit

    existente = Usuario.query.filter_by(username=username).first()

    if existente:
        print("Ese usuario ya existe.")
        raise SystemExit

    password_hash = generate_password_hash(password)

    usuario = Usuario(
        username=username,
        password_hash=password_hash,
        rol="ADMINISTRADOR",
        activo=True
    )

    db.session.add(usuario)
    db.session.commit()

    print("Administrador creado correctamente.")
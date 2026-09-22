from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from config import Config


db = SQLAlchemy()


app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.config.from_object(Config)

db.init_app(app)


@app.route("/")
def login():
    return render_template("login.html")


@app.route("/dashboard_admin")
def dashboard_admin():
    return render_template("dashboard_admin.html")


@app.route("/dashboard_gestor")
def dashboard_gestor():
    return render_template("dashboard_gestor.html")


@app.route("/dashboard_propietario")
def dashboard_propietario():
    return render_template("dashboard_propietario.html")


@app.route("/propietarios")
def propietarios():
    return render_template("propietarios.html")


@app.route("/inquilinos")
def inquilinos():
    return render_template("inquilinos.html")


@app.route("/propiedades")
def propiedades():
    return render_template("propiedades.html")


@app.route("/contratos")
def contratos():
    return render_template("contratos.html")


@app.route("/pagos")
def pagos():
    return render_template("pagos.html")


@app.route("/mantenimientos")
def mantenimientos():
    return render_template("mantenimientos.html")


@app.route("/proveedores")
def proveedores():
    return render_template("proveedores.html")


@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html")


@app.route("/propietarios/nuevo", methods=["GET", "POST"])
def nuevo_propietario():
    return render_template("nuevo_propietario.html")


@app.route("/inquilinos/nuevo", methods=["GET", "POST"])
def nuevo_inquilino():
    return render_template("nuevo_inquilino.html")


@app.route("/test-db")
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "Conexión a PostgreSQL exitosa."
    except Exception as e:
        return f"Error de conexión: {e}"


if __name__ == "__main__":
    app.run(debug=True)
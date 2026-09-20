from flask import Flask, render_template

app = Flask(__name__)


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


@app.route("/tecnicos")
def tecnicos():
    return render_template("tecnicos.html")


@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html")


if __name__ == "__main__":
    app.run(debug=True)
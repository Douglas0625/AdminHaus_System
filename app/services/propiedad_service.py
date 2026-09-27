from decimal import Decimal, InvalidOperation

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db

from app.models.propiedad import Propiedad
from app.models.propietario import Propietario
from app.models.fotografia import Fotografia


TIPOS_VALIDOS = ("CASA", "APARTAMENTO")
ESTADOS_VALIDOS = ("DISPONIBLE", "ALQUILADA", "INACTIVA")
FOTOGRAFIA_RUTA_MAX_LEN = 500


# =========================================================
# PROPIETARIO ASOCIADO AL USUARIO AUTENTICADO
# =========================================================

def obtener_propietario_por_usuario(usuario_id):
    """
    Devuelve el registro de Propietario asociado a un usuario
    autenticado con rol PROPIETARIO (usuario.id -> propietario.usuario_id).
    Devuelve None si el usuario no tiene un propietario asociado.
    """

    return Propietario.query.filter_by(usuario_id=usuario_id).first()


# =========================================================
# LISTADO / BÚSQUEDA
# =========================================================

def obtener_propiedades(usuario, buscar="", tipo="todos", estado="todos"):
    """
    Obtiene las propiedades visibles para el usuario autenticado.

    - ADMINISTRADOR y GESTOR: ven todas las propiedades.
    - PROPIETARIO: ve únicamente las propiedades que le pertenecen
      (a través de propietario.usuario_id).

    Permite buscar por código, dirección o municipio, y filtrar
    por tipo y estado. Toda la lógica de consulta vive aquí para
    que las rutas y los templates no construyan filtros.
    """

    query = Propiedad.query

    if usuario.rol == "PROPIETARIO":

        propietario = obtener_propietario_por_usuario(usuario.id)

        if propietario is None:
            return []

        query = query.filter(Propiedad.propietario_id == propietario.id)

    buscar = (buscar or "").strip()

    if buscar:

        patron = f"%{buscar}%"

        query = query.filter(
            or_(
                Propiedad.codigo.ilike(patron),
                Propiedad.direccion.ilike(patron),
                Propiedad.municipio.ilike(patron),
            )
        )

    if tipo and tipo != "todos" and tipo in TIPOS_VALIDOS:
        query = query.filter(Propiedad.tipo == tipo)

    if estado and estado != "todos" and estado in ESTADOS_VALIDOS:
        query = query.filter(Propiedad.estado == estado)

    return query.order_by(Propiedad.codigo).all()


# =========================================================
# OBTENER UNA PROPIEDAD
# =========================================================

def obtener_propiedad(propiedad_id):
    """
    Obtiene una propiedad por su id, sin filtrar por permisos.
    La verificación de autorización se hace aparte con
    'usuario_puede_acceder_propiedad', para mantener la
    autorización explícita en cada ruta.
    """

    return db.session.get(Propiedad, propiedad_id)


def usuario_puede_acceder_propiedad(usuario, propiedad):
    """
    Regla central de autorización para una propiedad puntual.

    - ADMINISTRADOR y GESTOR: pueden acceder a cualquier propiedad.
    - PROPIETARIO: solo puede acceder si la propiedad le pertenece
      (propiedad.propietario_id == propietario.id, donde el
      propietario se obtiene a partir de usuario.id).

    Esta función se llama siempre desde la ruta antes de mostrar
    o modificar datos: la autorización no depende de ocultar
    botones en el template.
    """

    if usuario.rol in ("ADMINISTRADOR", "GESTOR"):
        return True

    if usuario.rol == "PROPIETARIO":

        propietario = obtener_propietario_por_usuario(usuario.id)

        if propietario is None:
            return False

        return propiedad.propietario_id == propietario.id

    return False


# =========================================================
# DATOS AUXILIARES PARA FORMULARIOS
# =========================================================

def obtener_propietarios_para_select():
    """
    Todos los propietarios, para llenar el <select> del
    formulario de creación/edición de propiedades.
    """

    return Propietario.query.order_by(
        Propietario.apellido,
        Propietario.nombre,
    ).all()


# =========================================================
# VALIDACIÓN DE DATOS
# =========================================================

def _parsear_entero(valor, campo, errores):
    valor = (valor or "").strip()

    if valor == "":
        return 0

    try:
        numero = int(valor)
    except ValueError:
        errores.append(f"El campo '{campo}' debe ser un número entero.")
        return None

    if numero < 0:
        errores.append(f"El campo '{campo}' no puede ser negativo.")
        return None

    return numero


def _parsear_decimal(valor, campo, errores, requerido, permite_cero=True):
    valor = (valor or "").strip()

    if valor == "":
        if requerido:
            errores.append(f"El campo '{campo}' es obligatorio.")
        return None

    try:
        numero = Decimal(valor)
    except (InvalidOperation, ValueError):
        errores.append(f"El campo '{campo}' debe ser un número válido.")
        return None

    if numero < 0:
        errores.append(f"El campo '{campo}' no puede ser negativo.")
        return None

    if not permite_cero and numero == 0:
        errores.append(f"El campo '{campo}' debe ser mayor que cero.")
        return None

    return numero


def _validar_y_normalizar(datos, propiedad_id_excluir=None):
    """
    Valida y normaliza los datos recibidos desde el formulario.

    Devuelve una tupla (datos_normalizados, errores).
    'datos_normalizados' es un diccionario listo para crear o
    actualizar una Propiedad; 'errores' es una lista de mensajes
    (vacía si todo es válido).
    """

    errores = []

    codigo = (datos.get("codigo") or "").strip()
    tipo = (datos.get("tipo") or "").strip().upper()
    direccion = (datos.get("direccion") or "").strip()
    municipio = (datos.get("municipio") or "").strip()
    departamento = (datos.get("departamento") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    estado = (datos.get("estado") or "DISPONIBLE").strip().upper()
    propietario_id = (datos.get("propietario_id") or "").strip()

    if not codigo:
        errores.append("El código es obligatorio.")

    if not direccion:
        errores.append("La dirección es obligatoria.")

    if not municipio:
        errores.append("El municipio es obligatorio.")

    if not departamento:
        errores.append("El departamento es obligatorio.")

    if tipo not in TIPOS_VALIDOS:
        errores.append("El tipo debe ser CASA o APARTAMENTO.")

    if estado not in ESTADOS_VALIDOS:
        errores.append("El estado debe ser DISPONIBLE, ALQUILADA o INACTIVA.")

    propietario = None

    if not propietario_id:
        errores.append("El propietario es obligatorio.")
    else:
        try:
            propietario = db.session.get(Propietario, int(propietario_id))
        except ValueError:
            propietario = None

        if propietario is None:
            errores.append("El propietario seleccionado no existe.")

    habitaciones = _parsear_entero(datos.get("habitaciones"), "habitaciones", errores)
    banos = _parsear_entero(datos.get("banos"), "baños", errores)
    parqueos = _parsear_entero(datos.get("parqueos"), "parqueos", errores)

    metros_cuadrados = _parsear_decimal(
        datos.get("metros_cuadrados"),
        "metros cuadrados",
        errores,
        requerido=False,
        permite_cero=False,
    )

    precio_alquiler = _parsear_decimal(
        datos.get("precio_alquiler"),
        "precio de alquiler",
        errores,
        requerido=True,
        permite_cero=True,
    )

    # Código duplicado (además de la restricción UNIQUE en la BD).
    if codigo:

        query_codigo = Propiedad.query.filter(Propiedad.codigo == codigo)

        if propiedad_id_excluir is not None:
            query_codigo = query_codigo.filter(Propiedad.id != propiedad_id_excluir)

        if query_codigo.first() is not None:
            errores.append("Ya existe una propiedad con ese código.")

    if errores:
        return None, errores

    normalizados = {
        "codigo": codigo,
        "tipo": tipo,
        "direccion": direccion,
        "municipio": municipio,
        "departamento": departamento,
        "descripcion": descripcion or None,
        "habitaciones": habitaciones or 0,
        "banos": banos or 0,
        "parqueos": parqueos or 0,
        "metros_cuadrados": metros_cuadrados,
        "precio_alquiler": precio_alquiler,
        "estado": estado,
        "propietario_id": propietario.id,
    }

    return normalizados, []


# =========================================================
# CREAR
# =========================================================

def crear_propiedad(datos):
    """
    Crea una nueva propiedad a partir de los datos del formulario.
    Devuelve una tupla (propiedad, errores):
    - Si errores está vacío, la propiedad se guardó correctamente.
    - Si hay errores, no se guardó nada.
    """

    normalizados, errores = _validar_y_normalizar(datos)

    if errores:
        return None, errores

    propiedad = Propiedad(**normalizados)

    db.session.add(propiedad)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, ["Ya existe una propiedad con ese código."]

    return propiedad, []


# =========================================================
# ACTUALIZAR
# =========================================================

def actualizar_propiedad(propiedad, datos):
    """
    Actualiza una propiedad existente a partir de los datos del
    formulario. Devuelve (ok, errores).
    """

    normalizados, errores = _validar_y_normalizar(
        datos,
        propiedad_id_excluir=propiedad.id,
    )

    if errores:
        return False, errores

    for campo, valor in normalizados.items():
        setattr(propiedad, campo, valor)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False, ["Ya existe una propiedad con ese código."]

    return True, []


# =========================================================
# FOTOGRAFÍAS (URL EXTERNA)
# =========================================================
# La BD no almacena archivos: 'ruta' guarda la URL externa que
# el usuario ingresa (por ejemplo, un enlace a una imagen ya
# alojada en internet). No hay subida ni procesamiento de archivos.

def _limpiar_urls_fotografias(urls):
    """
    Valida una lista de URLs recibidas del formulario.
    Las URLs vacías se ignoran (campo opcional). Devuelve
    (urls_validas, errores); una URL con formato inválido no
    detiene el guardado de la propiedad, solo se reporta.
    """

    urls_validas = []
    errores = []

    for url in urls:
        url = (url or "").strip()

        if not url:
            continue

        if not (url.startswith("http://") or url.startswith("https://")):
            errores.append(
                f"La URL '{url}' no es válida (debe iniciar con http:// o https://)."
            )
            continue

        if len(url) > FOTOGRAFIA_RUTA_MAX_LEN:
            errores.append(
                f"Una de las URLs de fotografía supera los {FOTOGRAFIA_RUTA_MAX_LEN} caracteres permitidos."
            )
            continue

        urls_validas.append(url)

    return urls_validas, errores


def agregar_fotografias(propiedad, urls):
    """
    Agrega fotografías (por URL externa) a una propiedad ya
    existente. Devuelve la lista de errores (vacía si todo
    salió bien); las URLs válidas siempre se guardan aunque
    alguna otra URL de la misma lista sea inválida.
    """

    urls_validas, errores = _limpiar_urls_fotografias(urls)

    for url in urls_validas:
        db.session.add(Fotografia(propiedad_id=propiedad.id, ruta=url))

    if urls_validas:
        db.session.commit()

    return errores


def eliminar_fotografias(propiedad, fotografia_ids):
    """
    Elimina fotografías de una propiedad. Verifica que cada
    fotografía pertenezca realmente a esa propiedad, para que
    no se pueda borrar la foto de otra propiedad manipulando
    el formulario.
    """

    ids_validos = []

    for valor in fotografia_ids:
        try:
            ids_validos.append(int(valor))
        except (TypeError, ValueError):
            continue

    if not ids_validos:
        return

    Fotografia.query.filter(
        Fotografia.id.in_(ids_validos),
        Fotografia.propiedad_id == propiedad.id,
    ).delete(synchronize_session=False)

    db.session.commit()

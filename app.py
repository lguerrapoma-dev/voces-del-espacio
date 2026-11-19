
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
    send_file
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =====================================================
# 1. INICIALIZACIÓN DE EXTENSIONES
# =====================================================

db = SQLAlchemy()
login_manager = LoginManager()


# =====================================================
# 2. MODELO DE USUARIO
# =====================================================

class User(UserMixin, db.Model):

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    nombres = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    rol = db.Column(
        db.String(20),
        default="ALUMNO",
        nullable=False
    )

    historias = db.relationship(
        "Story",
        backref="autor",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def establecer_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):
        return check_password_hash(self.password_hash, password)


# =====================================================
# 3. MODELO DE HISTORIAS
# =====================================================

class Story(db.Model):

    __tablename__ = "historias"

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    contenido = db.Column(
        db.Text,
        nullable=False
    )

    planeta = db.Column(
        db.String(100),
        default="Marte"
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )


# =====================================================
# 4. CARGA DE USUARIOS
# =====================================================

@login_manager.user_loader
def cargar_usuario(user_id):

    return db.session.get(User, int(user_id))


# =====================================================
# 5. CONTROL DE ACCESO ADMINISTRADOR
# =====================================================

def administrador_requerido(funcion):

    @wraps(funcion)
    @login_required
    def decorador(*args, **kwargs):

        if current_user.rol != "ADMIN":
            abort(403)

        return funcion(*args, **kwargs)

    return decorador


# =====================================================
# 6. FACTORY DE LA APLICACIÓN
# =====================================================

def create_app(test_config=None):

    app = Flask(__name__)

    # CONFIGURACIÓN GENERAL

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "clave-desarrollo-voces-del-espacio"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(
            app.instance_path,
            "voces_del_espacio.db"
        )
    ).replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    # INICIALIZAR EXTENSIONES

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "login"

    login_manager.login_message = (
        "Debes iniciar sesión para acceder a esta sección."
    )

    # =================================================
    # 7. RUTA PRINCIPAL
    # =================================================

    @app.route("/")
    def index():

        archivo = os.path.join(
            app.root_path,
            "templates",
            "index.html"
        )

        return send_file(archivo)

    # =================================================
    # 8. REGISTRO DE USUARIOS
    # =================================================

    @app.route("/registro", methods=["GET", "POST"])
    def registro():

        if request.method == "POST":

            username = request.form.get(
                "username", ""
            ).strip()

            nombres = request.form.get(
                "nombres", ""
            ).strip()

            email = request.form.get(
                "email", ""
            ).strip().lower()

            password = request.form.get("password", "")

            if not all([username, nombres, email, password]):

                flash("Completa todos los campos.", "danger")

                return redirect(url_for("registro"))

            if User.query.filter_by(username=username).first():

                flash("El usuario ya existe.", "danger")

                return redirect(url_for("registro"))

            if User.query.filter_by(email=email).first():

                flash("El correo ya está registrado.", "danger")

                return redirect(url_for("registro"))

            usuario = User(
                username=username,
                nombres=nombres,
                email=email,
                rol="ALUMNO"
            )

            usuario.establecer_password(password)

            db.session.add(usuario)

            db.session.commit()

            flash(
                "Registro exitoso. Ya puedes iniciar sesión.",
                "success"
            )

            return redirect(url_for("login"))

        return render_template(
            "auth.html",
            accion="registro"
        )

    # =================================================
    # 9. INICIO DE SESIÓN
    # =================================================

    @app.route("/login", methods=["GET", "POST"])
    def login():

        if request.method == "POST":

            username = request.form.get(
                "username", ""
            ).strip()

            password = request.form.get("password", "")

            usuario = User.query.filter_by(
                username=username
            ).first()

            if usuario and usuario.verificar_password(password):

                login_user(usuario)

                flash(
                    "Bienvenido a Voces del Espacio.",
                    "success"
                )

                return redirect(url_for("dashboard"))

            flash(
                "Usuario o contraseña incorrectos.",
                "danger"
            )

        return render_template(
            "auth.html",
            accion="login"
        )

    # =================================================
    # 10. CERRAR SESIÓN
    # =================================================

    @app.route("/logout")
    @login_required
    def logout():

        logout_user()

        flash(
            "Sesión cerrada correctamente.",
            "success"
        )

        return redirect(url_for("index"))

    # =================================================
    # 11. PANEL DEL USUARIO
    # =================================================

    @app.route("/dashboard")
    @login_required
    def dashboard():

        historias = Story.query.order_by(
            Story.fecha_creacion.desc()
        ).all()

        return render_template(
            "dashboard.html",
            historias=historias
        )

    # =================================================
    # 12. PANEL ADMINISTRADOR
    # =================================================

    @app.route("/admin")
    @administrador_requerido
    def admin():

        usuarios = User.query.order_by(
            User.id.desc()
        ).all()

        historias = Story.query.order_by(
            Story.fecha_creacion.desc()
        ).all()

        return render_template(
            "admin.html",
            usuarios=usuarios,
            historias=historias
        )

    # =================================================
    # 13. CREAR HISTORIA
    # =================================================

    @app.route("/historias/crear", methods=["POST"])
    @login_required
    def crear_historia():

        titulo = request.form.get(
            "titulo", ""
        ).strip()

        contenido = request.form.get(
            "contenido", ""
        ).strip()

        planeta = request.form.get(
            "planeta", "Marte"
        ).strip()

        if not titulo or not contenido:

            flash(
                "Debes completar el título y el contenido.",
                "danger"
            )

            return redirect(url_for("dashboard"))

        historia = Story(
            titulo=titulo,
            contenido=contenido,
            planeta=planeta,
            usuario_id=current_user.id
        )

        db.session.add(historia)

        db.session.commit()

        flash(
            "Historia publicada correctamente.",
            "success"
        )

        return redirect(url_for("dashboard"))

    # =================================================
    # 14. EDITAR HISTORIA
    # =================================================

    @app.route(
        "/historias/editar/<int:id>",
        methods=["GET", "POST"]
    )
    @login_required
    def editar_historia(id):

        historia = db.get_or_404(Story, id)

        if (
            current_user.rol != "ADMIN"
            and historia.usuario_id != current_user.id
        ):
            abort(403)

        if request.method == "POST":

            historia.titulo = request.form.get(
                "titulo", ""
            ).strip()

            historia.contenido = request.form.get(
                "contenido", ""
            ).strip()

            historia.planeta = request.form.get(
                "planeta", "Marte"
            ).strip()

            db.session.commit()

            flash(
                "Historia actualizada correctamente.",
                "success"
            )

            return redirect(url_for("dashboard"))

        return render_template(
            "dashboard.html",
            historias=Story.query.order_by(
                Story.fecha_creacion.desc()
            ).all(),
            historia_editar=historia
        )

    # =================================================
    # 15. ELIMINAR HISTORIA
    # =================================================

    @app.route(
        "/historias/eliminar/<int:id>",
        methods=["POST"]
    )
    @login_required
    def eliminar_historia(id):

        historia = db.get_or_404(Story, id)

        if (
            current_user.rol != "ADMIN"
            and historia.usuario_id != current_user.id
        ):
            abort(403)

        db.session.delete(historia)

        db.session.commit()

        flash(
            "Historia eliminada correctamente.",
            "success"
        )

        return redirect(url_for("dashboard"))

    # =================================================
    # 16. API DE HISTORIAS
    # =================================================

    @app.route("/api/historias", methods=["GET"])
    def api_historias():

        historias = Story.query.order_by(
            Story.fecha_creacion.desc()
        ).all()

        resultado = []

        for historia in historias:

            resultado.append({

                "id": historia.id,

                "titulo": historia.titulo,

                "contenido": historia.contenido,

                "planeta": historia.planeta,

                "autor": historia.autor.nombres,

                "fecha": historia.fecha_creacion.isoformat()

            })

        return jsonify(resultado)

    # =================================================
    # 17. CAMBIAR ROL DE USUARIO
    # =================================================

    @app.route(
        "/admin/usuario/<int:id>/rol",
        methods=["POST"]
    )
    @administrador_requerido
    def cambiar_rol(id):

        usuario = db.get_or_404(User, id)

        nuevo_rol = request.form.get(
            "rol", ""
        ).upper()

        if nuevo_rol not in ["ADMIN", "ALUMNO"]:

            flash("Rol no válido.", "danger")

            return redirect(url_for("admin"))

        usuario.rol = nuevo_rol

        db.session.commit()

        flash(
            "Rol actualizado correctamente.",
            "success"
        )

        return redirect(url_for("admin"))

    # =================================================
    # 18. CREACIÓN DE BASE DE DATOS
    # =================================================

    with app.app_context():

        db.create_all()

        admin_username = os.environ.get("ADMIN_USERNAME")

        admin_email = os.environ.get("ADMIN_EMAIL")

        admin_password = os.environ.get("ADMIN_PASSWORD")

        if admin_username and admin_email and admin_password:

            administrador = User.query.filter_by(
                username=admin_username
            ).first()

            if not administrador:

                administrador = User(
                    username=admin_username,
                    nombres="Administrador",
                    email=admin_email,
                    rol="ADMIN"
                )

                administrador.establecer_password(
                    admin_password
                )

                db.session.add(administrador)

                db.session.commit()

    return app


# =====================================================
# 19. CREACIÓN DE LA APLICACIÓN
# =====================================================

app = create_app()


# =====================================================
# 20. EJECUCIÓN DEL SERVIDOR
# =====================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

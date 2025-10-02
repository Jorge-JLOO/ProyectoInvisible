from flask import Flask, render_template, request, redirect, send_file, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate
import requests
import uuid
import os

# --- Configuración básica ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecretkey')

# Base de datos: Postgres en Render o SQLite en local
db_url = os.environ.get('DATABASE_URL') or 'sqlite:///educativo.db'
db_url = db_url.replace("postgres://", "postgresql://")  # Fix heroku-like URLs
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Login Manager ---#
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "⚠️ Debes iniciar sesión para acceder a esta sección"
login_manager.login_message_category = "warning"


# --- Modelos ---
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # "admin" o "user"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- Decorador para admin ---
def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("⚠️ Debes iniciar sesión", "warning")
            return redirect(url_for('login'))
        if getattr(current_user, "role", "user") != "admin":
            flash("❌ No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapped

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    telefono = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    curso = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estudiante = db.relationship('Estudiante', backref=db.backref('matriculas', lazy=True))

class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=True)
    deuda_id = db.Column(db.Integer, db.ForeignKey('deuda.id'), nullable=True)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estudiante = db.relationship('Estudiante', backref=db.backref('pagos', lazy=True))
    deuda = db.relationship('Deuda', backref=db.backref('pagos', lazy=True))

class Deuda(db.Model):
    __tablename__ = 'deuda'
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    concepto = db.Column(db.String(100), nullable=False)
    monto_total = db.Column(db.Float, nullable=False)
    saldo_pendiente = db.Column(db.Float, nullable=False)
    estudiante = db.relationship('Estudiante', backref=db.backref('deudas', lazy=True))

# --- Context Processor ---
@app.context_processor
def inject_now():
    return {'current_year': datetime.utcnow().year, 'current_user': current_user}

# ------------------- RUTAS -------------------

@app.route('/')
def index():
    return render_template('index.html')

# --- Login ---
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Bienvenido/a", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Enrollment ---
@app.route('/enrollment', methods=['GET','POST'])
def enrollment():
    if request.method == 'POST':
        nombre = request.form.get('nombre','').strip()
        documento = request.form.get('documento','').strip()
        curso = request.form.get('curso','').strip()
        telefono = request.form.get('telefono','').strip()

        if not nombre or not documento or not curso:
            flash('Nombre, documento y curso son obligatorios','danger')
            return redirect(url_for('enrollment'))

        estudiante = Estudiante.query.filter_by(documento=documento).first()
        if not estudiante:
            try:
                estudiante = Estudiante(nombre=nombre, documento=documento, telefono=telefono)
                db.session.add(estudiante)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('El documento ya existe en el sistema','danger')
                return redirect(url_for('enrollment'))

        matricula = Matricula(estudiante_id=estudiante.id, curso=curso)
        db.session.add(matricula)
        db.session.commit()
        flash('Matrícula registrada correctamente','success')
        return redirect(url_for('index'))

    return render_template('enrollment.html')

# --- Payment / búsqueda de estudiante y deudas ---
@app.route('/payment', methods=['GET','POST'])
def payment():
    estudiante = None
    deudas = []
    if request.method == 'POST':
        documento = request.form.get('documento','').strip()
        if not documento:
            flash("Ingrese un documento para buscar", "warning")
            return redirect(url_for('payment'))

        estudiante = Estudiante.query.filter_by(documento=documento).first()
        if not estudiante:
            flash("Estudiante no encontrado", "danger")
            return render_template('payment.html', estudiante=None, deudas=[])
        deudas = Deuda.query.filter_by(estudiante_id=estudiante.id).filter(Deuda.saldo_pendiente > 0).order_by(Deuda.id.desc()).all()

    return render_template('payment.html', estudiante=estudiante, deudas=deudas)

@app.route('/registrar_pago/<int:deuda_id>', methods=['POST'])
def registrar_pago(deuda_id):
    deuda = Deuda.query.get_or_404(deuda_id)
    try:
        valor = float(request.form.get('valor', '0'))
    except ValueError:
        flash("Valor inválido", "danger")
        return redirect(url_for('payment'))

    metodo = request.form.get('metodo', 'Efectivo')
    if valor <= 0:
        flash("Valor debe ser mayor que 0", "warning")
        return redirect(url_for('payment'))

    if valor > deuda.saldo_pendiente + 0.0001:
        flash("El valor no puede ser mayor que el saldo pendiente", "warning")
        return redirect(url_for('payment'))

    pago = Pago(estudiante_id=deuda.estudiante_id, deuda_id=deuda.id, valor=valor, metodo=metodo)
    db.session.add(pago)
    deuda.saldo_pendiente = max(0.0, deuda.saldo_pendiente - valor)
    db.session.commit()

    flash("Pago registrado correctamente", "success")

    # Factura PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(300, 760, "Factura de Pago - Proyecto Educativo")
    c.setFont("Helvetica", 11)
    c.drawString(50, 720, f"Factura ID: {pago.id}")
    c.drawString(50, 700, f"Fecha: {pago.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    est = deuda.estudiante
    c.drawString(50, 680, f"Nombre: {est.nombre}")
    c.drawString(50, 660, f"Documento: {est.documento}")
    c.drawString(50, 640, f"Concepto deuda: {deuda.concepto}")
    c.drawString(50, 620, f"Método de pago: {pago.metodo}")
    c.drawString(50, 600, f"Valor pagado: ${pago.valor:,.2f}")
    c.drawString(50, 580, f"Saldo pendiente deuda: ${deuda.saldo_pendiente:,.2f}")
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f'factura_{pago.id}.pdf', mimetype='application/pdf')

# --- Consulta ---
@app.route('/consulta', methods=['GET','POST'])
@login_required
def consulta():
    estudiante = None
    if request.method == 'POST':
        documento = request.form.get('documento')
        estudiante = Estudiante.query.filter_by(documento=documento).first()
    return render_template('consulta.html', estudiante=estudiante)


# --- Admin ---
@app.route('/admin')
@admin_required
@login_required
def admin():
    estudiantes = Estudiante.query.order_by(Estudiante.nombre).all()
    matriculas = Matricula.query.order_by(Matricula.fecha.desc()).all()
    pagos = Pago.query.order_by(Pago.fecha.desc()).all()
    deudas = Deuda.query.order_by(Deuda.id.desc()).all()
    return render_template("admin.html",
                           estudiantes=estudiantes,
                           matriculas=matriculas,
                           pagos=pagos,
                           deudas=deudas)


@app.route('/admin/estudiante/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        estudiante.nombre = request.form['nombre']
        estudiante.documento = request.form['documento']
        estudiante.telefono = request.form['telefono']
        db.session.commit()
        flash('Estudiante actualizado correctamente', 'success')
        return redirect(url_for('admin'))
    return render_template('editar_estudiante.html', estudiante=estudiante)

@app.route('/admin/crear_estudiante', methods=['POST'])
@login_required
def crear_estudiante():
    nombre = request.form['nombre']
    documento = request.form['documento']
    telefono = request.form.get('telefono')
    if not nombre or not documento:
        flash("Nombre y documento son obligatorios", "danger")
        return redirect(url_for('admin'))
    nuevo = Estudiante(nombre=nombre, documento=documento, telefono=telefono)
    db.session.add(nuevo)
    db.session.commit()
    flash("Estudiante creado correctamente", "success")
    return redirect(url_for('admin'))

@app.route('/admin/estudiante/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    estudiante.activo = not estudiante.activo
    db.session.commit()
    estado = "activado" if estudiante.activo else "inactivado"
    flash(f'Estudiante {estado} correctamente', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/crear_deuda', methods=['POST'])
@login_required
def crear_deuda():
    estudiante_id = request.form.get('estudiante_id')
    concepto = request.form.get('concepto')
    monto = float(request.form.get('monto', '0') or 0)
    if not estudiante_id or monto <= 0 or not concepto:
        flash("Datos inválidos para crear deuda", "danger")
        return redirect(url_for('admin'))
    deuda = Deuda(estudiante_id=estudiante_id, concepto=concepto, monto_total=monto, saldo_pendiente=monto)
    db.session.add(deuda)
    db.session.commit()
    flash("Deuda registrada correctamente", "success")
    return redirect(url_for('admin'))

# --- Cambiar contraseña ---
@app.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        actual = request.form['actual']
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']

        if not check_password_hash(current_user.password, actual):
            flash('❌ La contraseña actual no es correcta', 'danger')
            return redirect(url_for('cambiar_password'))

        if nueva != confirmar:
            flash('⚠️ La nueva contraseña y la confirmación no coinciden', 'warning')
            return redirect(url_for('cambiar_password'))

        current_user.password = generate_password_hash(nueva)
        db.session.commit()
        flash('✅ Contraseña actualizada con éxito', 'success')
        return redirect(url_for('admin'))

    return render_template('cambiar_password.html')

# --- Rutas extra ---
@app.route('/pago_efectivo')
def pago_efectivo():
    return redirect(url_for('payment'))

@app.route('/pago_online', methods=['GET', 'POST'])
def pago_online():
    if request.method == 'POST':
        flash("Integración con pasarela (Wompi) pendiente / configurada en variables de entorno", "info")
        return redirect(url_for('payment'))
    return render_template('pago_online.html')

@app.route('/confirmacion_pago')
def confirmacion_pago():
    flash("✅ Gracias, tu pago está siendo procesado", "success")
    return redirect(url_for("index"))

# --- MAIN ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)

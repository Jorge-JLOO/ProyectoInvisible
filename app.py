from flask import Flask, render_template, request, redirect, send_file, url_for, flash
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY','devsecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///educativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 🔹 Crear las tablas al arrancar, incluso en Render (gunicorn)
with app.app_context():
    db.create_all()

@app.context_processor
def inject_now():
    return {'current_year': datetime.utcnow().year}

# Models
class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    telefono = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)  # 👈 NUEVO CAMPO

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    curso = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estudiante = db.relationship('Estudiante', backref=db.backref('matriculas', lazy=True))

class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estudiante = db.relationship('Estudiante', backref=db.backref('pagos', lazy=True))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Enrollment
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

# Payment
@app.route('/payment', methods=['GET','POST'])
def payment():
    if request.method == 'POST':
        nombre = request.form.get('nombre','').strip()
        documento = request.form.get('documento','').strip()
        valor = request.form.get('valor','0').strip()
        metodo = request.form.get('metodo','').strip()
        telefono = request.form.get('telefono','').strip()

        try:
            valor_f = float(valor)
        except ValueError:
            flash('Valor inválido','danger')
            return redirect(url_for('payment'))

        if not nombre or not documento or not metodo:
            flash('Nombre, documento y método son obligatorios','danger')
            return redirect(url_for('payment'))

        try:
            estudiante = Estudiante.query.filter_by(documento=documento).first()
            if not estudiante:
                estudiante = Estudiante(nombre=nombre, documento=documento, telefono=telefono)
                db.session.add(estudiante)
                db.session.commit()
        except IntegrityError:
            db.session.rollback()
            estudiante = Estudiante.query.filter_by(documento=documento).first()

        # Registrar pago
        pago = Pago(estudiante_id=estudiante.id, valor=valor_f, metodo=metodo)
        db.session.add(pago)
        db.session.commit()

        # Generar PDF factura
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, 760, "Factura de Pago - Proyecto Educativo")
        c.setFont("Helvetica", 11)
        c.drawString(50, 720, f"Factura ID: {pago.id}")
        c.drawString(50, 700, f"Fecha: {pago.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(50, 680, f"Nombre: {estudiante.nombre}")
        c.drawString(50, 660, f"Documento: {estudiante.documento}")
        c.drawString(50, 640, f"Teléfono: {estudiante.telefono or ''}")
        c.drawString(50, 620, f"Método de pago: {pago.metodo}")
        c.drawString(50, 600, f"Valor: ${pago.valor:,.2f}")
        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'factura_{pago.id}.pdf', mimetype='application/pdf')

    return render_template('payment.html')

# Admin list (simple)
@app.route('/admin')
def admin():
    estudiantes = Estudiante.query.order_by(Estudiante.nombre).all()
    matriculas = Matricula.query.order_by(Matricula.fecha.desc()).all()
    pagos = Pago.query.order_by(Pago.fecha.desc()).all()
    return render_template('admin.html', estudiantes=estudiantes, matriculas=matriculas, pagos=pagos)

# Editar estudiante
@app.route('/admin/estudiante/<int:id>/editar', methods=['GET', 'POST'])
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

# Eliminar estudiante
@app.route('/admin/estudiante/<int:id>/eliminar', methods=['POST'])
def eliminar_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    db.session.delete(estudiante)
    db.session.commit()
    flash('Estudiante eliminado correctamente', 'warning')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)

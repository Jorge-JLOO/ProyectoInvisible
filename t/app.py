from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///educativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------------
# MODELOS
# ------------------------
class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    curso = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------------
# RUTAS
# ------------------------

@app.route('/')
def index():
    return render_template('index.html')

# MATRÍCULAS
@app.route('/enrollment', methods=['GET', 'POST'])
def enrollment():
    if request.method == 'POST':
        nombre = request.form['nombre']
        documento = request.form['documento']
        curso = request.form['curso']

        # Buscar si el estudiante ya existe
        estudiante = Estudiante.query.filter_by(documento=documento).first()
        if not estudiante:
            estudiante = Estudiante(nombre=nombre, documento=documento)
            db.session.add(estudiante)
            db.session.commit()

        matricula = Matricula(estudiante_id=estudiante.id, curso=curso)
        db.session.add(matricula)
        db.session.commit()

        return redirect('/')
    return render_template('enrollment.html')

# PAGOS
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        nombre = request.form['nombre']
        documento = request.form['documento']
        valor = float(request.form['valor'])
        metodo = request.form['metodo']

        # Buscar si el estudiante existe
        estudiante = Estudiante.query.filter_by(documento=documento).first()
        if not estudiante:
            estudiante = Estudiante(nombre=nombre, documento=documento)
            db.session.add(estudiante)
            db.session.commit()

        pago = Pago(estudiante_id=estudiante.id, valor=valor, metodo=metodo)
        db.session.add(pago)
        db.session.commit()

        # Generar PDF de la factura
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Factura de Pago - Proyecto Educativo")
        c.drawString(100, 720, f"Estudiante: {estudiante.nombre}")
        c.drawString(100, 700, f"Documento: {estudiante.documento}")
        c.drawString(100, 680, f"Valor: ${valor:,.2f}")
        c.drawString(100, 660, f"Método de pago: {metodo}")
        c.drawString(100, 640, f"Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}")
        c.showPage()
        c.save()

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="factura.pdf", mimetype="application/pdf")

    return render_template('payment.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
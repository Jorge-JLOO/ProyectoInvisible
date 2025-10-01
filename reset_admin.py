# reset_admin.py
from app import app, db, Usuario
from werkzeug.security import generate_password_hash

# --- Configuración del admin ---
USERNAME = "JorgeJLOO"   # cámbialo si quieres otro
PASSWORD = "5607"        # cámbialo si quieres otra

with app.app_context():
    # Eliminar usuario con mismo username
    Usuario.query.filter_by(username=USERNAME).delete()
    db.session.commit()

    # Crear admin nuevo
    admin = Usuario(
        username=USERNAME,
        password=generate_password_hash(PASSWORD),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()

    print(f"✅ Usuario administrador '{USERNAME}' creado con contraseña: {PASSWORD}")

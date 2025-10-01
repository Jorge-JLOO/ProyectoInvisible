from app import app, db, Usuario
from werkzeug.security import generate_password_hash

# 🚀 Usuario y contraseña para el admin
USERNAME = "admin"
PASSWORD = "admin123"   # 🔒 cámbiala si quieres

with app.app_context():
    admin = Usuario.query.filter_by(username=USERNAME).first()
    if not admin:
        admin = Usuario(username=USERNAME,
                        password=generate_password_hash(PASSWORD),
                        role="admin")   # 👈 importante
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario administrador '{USERNAME}' creado con contraseña: {PASSWORD}")
    else:
        admin.password = generate_password_hash(PASSWORD)
        admin.role = "admin"   # 👈 aseguramos que tenga rol admin
        db.session.commit()
        print(f"🔑 Contraseña del administrador '{USERNAME}' actualizada con éxito.")
from app import app, db, Usuario
from werkzeug.security import generate_password_hash

# 🚀 Contraseña fija que puedes cambiar aquí cuando quieras
USERNAME = "admin"
PASSWORD = "admin123"   # 🔒 cámbiala y vuelve a ejecutar el script para actualizarla

with app.app_context():
    admin = Usuario.query.filter_by(username=USERNAME).first()
    if not admin:
        admin = Usuario(username=USERNAME, password=generate_password_hash(PASSWORD))
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario administrador '{USERNAME}' creado con contraseña: {PASSWORD}")
    else:
        admin.password = generate_password_hash(PASSWORD)
        db.session.commit()
        print(f"🔑 Contraseña del administrador '{USERNAME}' actualizada con éxito.")
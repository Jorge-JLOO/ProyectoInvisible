from app import app, db, Usuario
from werkzeug.security import generate_password_hash

USERNAME = "admin"
PASSWORD = "admin123"   # la que tú quieras

with app.app_context():
    Usuario.query.filter_by(username=USERNAME).delete()
    db.session.commit()

    admin = Usuario(username=USERNAME, password=generate_password_hash(PASSWORD), role="admin")
    db.session.add(admin)
    db.session.commit()

    print(f"✅ Usuario administrador '{USERNAME}' creado con contraseña: {PASSWORD}")
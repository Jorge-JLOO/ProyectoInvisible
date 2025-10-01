from app import app, db, Usuario
from werkzeug.security import generate_password_hash

USERNAME = "JorgeJLOO"
PASSWORD = "5607"   # cámbiala aquí si quieres otra

with app.app_context():
    # eliminar cualquier admin existente
    Usuario.query.filter_by(username=USERNAME).delete()
    db.session.commit()

    # crear uno nuevo limpio
    admin = Usuario(
        username=USERNAME,
        password=generate_password_hash(PASSWORD),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()

    print(f"✅ Usuario administrador '{USERNAME}' creado con contraseña: {PASSWORD}")
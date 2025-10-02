from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def reset_admin():
    username = "admin"
    password = "1234"  # 👈 nueva contraseña
    role = "admin"

    with app.app_context():  # ✅ Esto crea el contexto correcto
        admin = Usuario.query.filter_by(username=username).first()
        if admin:
            admin.password_hash = generate_password_hash(password)
            admin.role = role
            print(f"✅ Contraseña de '{username}' actualizada.")
        else:
            admin = Usuario(
                username=username,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(admin)
            print(f"✅ Usuario '{username}' creado.")
        db.session.commit()

if __name__ == "__main__":
    reset_admin()

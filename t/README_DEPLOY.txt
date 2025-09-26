Proyecto Educativo - Full package

Contenido del ZIP:
- app.py : aplicación Flask (backend + rutas + generación de PDF con fpdf)
- requirements.txt : dependencias (Flask, Flask-SQLAlchemy, fpdf)
- templates/ : plantillas HTML (index, register, pay, admin)
- static/ : CSS
- .env.example : variables de entorno
- README_DEPLOY.txt : explicación detallada (incluye opciones de hosting gratuitas sugeridas)

1) Cómo ejecutar localmente (rápido)
- Crear un entorno virtual:
    python -m venv venv
    source venv/bin/activate    # unix/mac
    venv\\Scripts\\activate     # windows
- Instalar dependencias:
    pip install -r requirements.txt
- Copiar .env.example a .env (opcional) y editar ADMIN_PASS y SECRET_KEY
- Crear la base de datos y ejecutar:
    python app.py
- Visitar http://127.0.0.1:5000 para ver la app.

2) Funcionalidades principales
- Registro de estudiantes (/register)
- Panel de administración (/admin) protegido por autenticación básica HTTP. Contraseña por defecto se configura en ADMIN_PASS de las variables de entorno.
- Pago simulado: /pay/<student_id> crea un registro de pago y permite descargar factura en PDF (/invoice/<payment_id>).
- PDF generado con la librería fpdf (archivo factura_{id}.pdf servido descargable).

3) Dependencias y porqué (referencias):
- Flask + Flask-SQLAlchemy: framework minimal para backend y ORM.
- fpdf (FPDF for Python): librería liviana para crear PDFs desde Python sin dependencias pesadas. Para alternativas más complejas se puede usar ReportLab o WeasyPrint (ver links en seccion de deployment).

4) Opciones de hosting gratuitas (recomendadas) — comprobadas en web (documentación):
- Render: permite desplegar aplicaciones Flask gratis para proyectos pequeños. Tutorial oficial: Render docs. (Recommend using a public GitHub repo and conectar a Render).
- Supabase + Vercel (Frontend static + Supabase as DB/auth): good modern stack for free-tier projects. Supabase tiene un plan gratuito apto para proyectos personales. (See Supabase pricing page).
- PythonAnywhere: hosting directo para apps Flask con plan gratuito (limitations).

Referencias (consultadas automáticamente):
- Render free deploy docs. (render.com). 
- Supabase pricing page. (supabase.com).
- Guides on generating PDFs in Python (fpdf/reportlab/weasyprint).

5) Notas sobre pagos reales
- Este proyecto incluye una simulación de pago. Para integrar pagos reales se recomienda usar Stripe (modo test primero) o PayPal. Eso requiere registrar cuentas y poner claves de API en variables de entorno, además de manejar webhooks para confirmar pagos.

6) Cómo desplegar en Render (resumen)
- Subir el repo a GitHub.
- Crear cuenta en render.com (free tier).
- Conectar el repo y crear un Web Service (Python).
- Definir build command: pip install -r requirements.txt
- Start command: gunicorn app:app
- Add environment variables in Render (SECRET_KEY, ADMIN_PASS).
- Deploy. Render free services sleep after inactivity and have limitations (OK for testing).

Si quieres que modifique algo o que integre Stripe para pagos reales, dime y lo hago.
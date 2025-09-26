ProyectoInvisible - paquete listo
Contenido:
- app.py
- requirements.txt
- templates/ (base, index, enrollment, payment, admin)
- static/style.css
- DB: sqlite file educativo.db will be created on first run

Instrucciones (Windows):
1) Mover la carpeta al lugar que quieras, por ejemplo E:\ProyectoInvisible
2) Abrir PowerShell o CMD en la carpeta y crear/activar entorno:
   py -m virtualenv venv
   venv\Scripts\activate
3) Instalar dependencias:
   pip install -r requirements.txt
4) Ejecutar:
   python app.py
5) Abrir navegador en http://127.0.0.1:5000

Notas:
- Cambia SECRET_KEY en variable de entorno para producción.
- Los pagos aquí son simulados; la factura PDF se genera localmente con ReportLab.
- Si quieres integrar Stripe o enviar factura por email, puedo hacerlo en la siguiente iteración.

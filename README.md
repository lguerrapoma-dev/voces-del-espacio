# VOCES DEL ESPACIO — aplicación Flask

Proyecto educativo NASA Space Apps: **“Abandonados pero no olvidados: historias sobre el equipo desechado de la NASA en la Luna y Marte”**.

## Qué incluye
- Sitio original `VOCES DEL ESPACIO` conservado como página de inicio (`templates/index.html`), con su diseño, contenido, idiomas, recursos embebidos y navegación.
- Backend Flask y base de datos SQLite mediante Flask-SQLAlchemy.
- Registro, inicio y cierre de sesión; contraseñas almacenadas mediante hash.
- Roles `ALUMNO` y `ADMIN`; las rutas administrativas están protegidas.
- CRUD de historias por región (Marte, Luna y Espacio profundo), administración de usuarios y endpoint JSON `/api/historias`.
- Pruebas automatizadas con Pytest.

## Ejecutar localmente (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY="una-clave-local-larga"
$env:ADMIN_EMAIL="admin@ejemplo.com"
$env:ADMIN_PASSWORD="UnaClaveSegura123"
$env:ADMIN_USERNAME="admin"
python app.py
```
Abrir http://127.0.0.1:5000. El administrador inicial se crea al iniciar si se definieron las tres variables `ADMIN_EMAIL`, `ADMIN_PASSWORD` y `ADMIN_USERNAME`.

## Pruebas
```powershell
pytest -q
```

## Publicar en GitHub
Crear un repositorio vacío y ejecutar desde esta carpeta:
```bash
git init
git add .
git commit -m "Primera versión Flask de Voces del Espacio"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

## Desplegar en Render
1. Subir el repositorio a GitHub.
2. En Render, crear un **Blueprint** desde el repositorio; detectará `render.yaml`.
3. Completar `ADMIN_EMAIL` y `ADMIN_PASSWORD` como variables secretas al crear el servicio.
4. Esperar el despliegue y abrir la URL asignada.

**Nota de persistencia:** SQLite en el sistema de archivos efímero de un servicio web gratuito puede reiniciarse o perderse al volver a desplegar. Para producción en Render, configurar PostgreSQL o un disco persistente y cambiar `DATABASE_URL` a la URL de la base de datos. El proyecto ya admite `DATABASE_URL`.

## Estructura
```text
voces_del_espacio_flask/
├── app.py
├── templates/ (index original + autenticación + paneles)
├── tests/test_app.py
├── requirements.txt
├── Procfile
├── render.yaml
└── README.md
```

import pytest
import sys
from pathlib import Path

# Agregar la carpeta donde se encuentra app.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db, User, Story
from werkzeug.security import generate_password_hash

@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test", "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            db.session.add(User(username="admin", email="admin@test.com",
                password_hash=generate_password_hash("password123"), role="ADMIN"))
            db.session.commit()
        yield client
        with app.app_context(): db.drop_all()

def test_homepage(client):
    assert client.get("/").status_code == 200

def test_register_and_login(client):
    response = client.post("/registro", data={"username":"alumno","email":"a@test.com","password":"password123"}, follow_redirects=True)
    assert b"Cuenta creada" in response.data
    response = client.post("/login", data={"identity":"alumno","password":"password123"}, follow_redirects=True)
    assert response.status_code == 200 and b"Bienvenido" in response.data

def test_admin_can_create_story(client):
    client.post("/login", data={"identity":"admin","password":"password123"})
    response = client.post("/admin/historias", data={"title":"Rover lunar","region":"Luna","body":"Historia de prueba"}, follow_redirects=True)
    assert b"Rover lunar" in response.data
    assert client.get("/api/historias").json[0]["region"] == "Luna"

def test_student_cannot_access_admin(client):
    client.post("/registro", data={"username":"alumno","email":"a@test.com","password":"password123"})
    client.post("/login", data={"identity":"alumno","password":"password123"})
    assert client.get("/admin").status_code == 403

"""Тесты REST-эндпоинтов /auth/*."""

EMAIL = "flow@example.com"
PASSWORD = "correct horse battery staple 42"


def test_register_login_me(client):
    # Регистрация
    r = client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Логин
    r = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # /auth/me с токеном
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["email"] == EMAIL
    assert me["is_admin"] is False


def test_weak_password_not_registered(client):
    r = client.post("/auth/register", json={"email": "weak@example.com", "password": "short"})
    assert r.status_code == 400
    assert "12" in r.json()["detail"]  # сообщение про длину


def test_login_bad_password_returns_401(client):
    client.post("/auth/register", json={"email": "bad@example.com", "password": PASSWORD})
    r = client.post("/auth/login", json={"email": "bad@example.com", "password": "wrong-password"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"  # нейтральное сообщение


def test_me_without_token_returns_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_audit_event_on_login_success(client, db_session):
    from app.models import AuditEvent

    client.post("/auth/register", json={"email": "audit@example.com", "password": PASSWORD})
    client.post("/auth/login", json={"email": "audit@example.com", "password": PASSWORD})

    events = db_session.query(AuditEvent).all()
    types = [e.event_type for e in events]
    assert "user.created" in types
    assert "user.login.success" in types
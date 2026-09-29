"""Тесты GraphQL: доступ к защищённым полям."""

PASSWORD = "correct horse battery staple 42"
ADMIN_EMAIL = "gqladmin@example.com"
USER_EMAIL = "gqluser@example.com"


def _register_and_login(client, email):
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _gql(client, query, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/graphql/", json={"query": query}, headers=headers)


def test_me_without_token(client):
    r = _gql(client, "query { me { email } }")
    body = r.json()
    assert body.get("errors")
    assert body["errors"][0]["message"] == "Authentication required"


def test_me_with_token(client):
    token = _register_and_login(client, USER_EMAIL)
    r = _gql(client, "query { me { email isActive isAdmin } }", token=token)
    body = r.json()
    assert body.get("data"), body
    assert body["data"]["me"]["email"] == USER_EMAIL
    assert body["data"]["me"]["isActive"] is True
    assert body["data"]["me"]["isAdmin"] is False


def test_users_without_admin(client):
    token = _register_and_login(client, USER_EMAIL)
    r = _gql(client, "query { users { email } }", token=token)
    body = r.json()
    assert body.get("errors")
    assert body["errors"][0]["message"] == "Admin only"
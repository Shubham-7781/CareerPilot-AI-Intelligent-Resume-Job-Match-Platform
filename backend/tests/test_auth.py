def test_signup_success(client):
    resp = client.post("/api/auth/signup", json={
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "password": "strongpassword123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "jane@example.com"
    assert "hashed_password" not in data


def test_signup_duplicate_email_rejected(client):
    payload = {"full_name": "Jane", "email": "dupe@example.com", "password": "strongpassword123"}
    client.post("/api/auth/signup", json=payload)
    resp = client.post("/api/auth/signup", json=payload)
    assert resp.status_code == 409


def test_login_success_and_wrong_password(client):
    client.post("/api/auth/signup", json={
        "full_name": "Bob", "email": "bob@example.com", "password": "correcthorsebattery",
    })

    good = client.post("/api/auth/login", data={"username": "bob@example.com", "password": "correcthorsebattery"})
    assert good.status_code == 200
    assert "access_token" in good.json()

    bad = client.post("/api/auth/login", data={"username": "bob@example.com", "password": "wrongpass"})
    assert bad.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/resumes/")
    assert resp.status_code == 401


def test_password_is_hashed_not_plaintext(client, db_session):
    client.post("/api/auth/signup", json={
        "full_name": "Alice", "email": "alice@example.com", "password": "plaintextpassword",
    })
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "alice@example.com").first()
    assert user.hashed_password != "plaintextpassword"
    assert user.hashed_password.startswith("$2b$")

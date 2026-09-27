from datetime import datetime, timedelta


def _signup(client, email="verify@example.com"):
    return client.post("/api/auth/signup", json={
        "full_name": "Verify Me", "email": email, "password": "strongpassword123",
    })


def test_signup_creates_unverified_user_with_token(client, db_session):
    _signup(client)
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "verify@example.com").first()
    assert user.is_verified is False
    assert user.verification_token is not None


def test_verify_email_with_valid_token(client, db_session):
    _signup(client)
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "verify@example.com").first()

    resp = client.post("/api/auth/verify-email", json={"token": user.verification_token})
    assert resp.status_code == 200

    db_session.refresh(user)
    assert user.is_verified is True
    assert user.verification_token is None


def test_verify_email_with_invalid_token_rejected(client):
    resp = client.post("/api/auth/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


def test_verify_email_with_expired_token_rejected(client, db_session):
    _signup(client)
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "verify@example.com").first()
    user.verification_token_expires = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    resp = client.post("/api/auth/verify-email", json={"token": user.verification_token})
    assert resp.status_code == 400


def test_forgot_password_does_not_leak_account_existence(client):
    resp_existing = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp_existing.status_code == 200
    assert "sent" in resp_existing.json()["detail"].lower()


def test_reset_password_flow(client, db_session):
    _signup(client, email="reset@example.com")
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "reset@example.com").first()

    forgot = client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    assert forgot.status_code == 200

    db_session.refresh(user)
    assert user.reset_token is not None

    reset = client.post("/api/auth/reset-password", json={
        "token": user.reset_token, "new_password": "brandnewpassword123",
    })
    assert reset.status_code == 200

    login_old = client.post("/api/auth/login", data={"username": "reset@example.com", "password": "strongpassword123"})
    assert login_old.status_code == 401

    login_new = client.post("/api/auth/login", data={"username": "reset@example.com", "password": "brandnewpassword123"})
    assert login_new.status_code == 200


def test_reset_password_with_invalid_token_rejected(client):
    resp = client.post("/api/auth/reset-password", json={"token": "bad-token", "new_password": "whateverpassword123"})
    assert resp.status_code == 400

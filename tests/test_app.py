import re

from app.admin import _failed_logins
from app.extensions import db
from app.models import Submission


def _csrf(client, path="/admin/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _login(client, password="correct-horse-battery"):
    token = _csrf(client)
    return client.post("/admin/login", data={"username": "admin", "password": password, "csrf_token": token})


def test_index_shows_only_form(client):
    html = client.get("/").get_data(as_text=True)
    assert "<title>kartup</title>" in html and "Challenge Accepted" not in html
    assert html.count("<input") == 2
    assert 'id="name"' in html and 'id="surname"' in html
    assert ">Submit<" in html


def test_submit_saves_and_returns_only_confirmation(client, app):
    res = client.post("/api/submissions", json={"name": "  Ada ", "surname": "Lovelace"})
    assert res.status_code == 201
    body = res.get_json()
    assert body == {"ok": True, "message": "Thank you! Your details were submitted successfully."}
    with app.app_context():
        rows = db.session.scalars(db.select(Submission)).all()
        assert [(r.name, r.surname) for r in rows] == [("Ada", "Lovelace")]
        assert rows[0].created_at is not None


def test_validation_errors(client, app):
    res = client.post("/api/submissions", json={"name": "", "surname": "   "})
    assert res.status_code == 422
    errors = res.get_json()["errors"]
    assert set(errors) == {"name", "surname"}
    res = client.post("/api/submissions", json={"name": "A" * 101, "surname": "O'Brien"})
    assert set(res.get_json()["errors"]) == {"name"}
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Submission.id))) == 0


def test_accepts_any_characters(client, app):
    for name, surname in [("Jean-Luc", "Ñúñez"), ("R2D2", "user@example.com"), ("#1 fan!", "12345")]:
        assert client.post("/api/submissions", json={"name": name, "surname": surname}).status_code == 201
    with app.app_context():
        assert db.session.scalar(db.select(Submission.surname).where(Submission.name == "R2D2")) == "user@example.com"


def test_rejects_non_json(client):
    assert client.post("/api/submissions", data={"name": "A", "surname": "B"}).status_code == 415


def test_sql_injection_is_stored_as_text(client, app):
    payload = "x'); DROP TABLE submissions;--"
    assert client.post("/api/submissions", json={"name": payload, "surname": "y"}).status_code == 201
    with app.app_context():
        assert db.session.scalar(db.select(Submission.name)) == payload


def test_no_public_listing(client):
    assert client.get("/api/submissions").status_code == 405


def test_admin_requires_login(client):
    res = client.get("/admin/")
    assert res.status_code == 302 and "/admin/login" in res.headers["Location"]


def test_admin_rejects_bad_password(client):
    _failed_logins.clear()
    assert _login(client, "wrong").status_code == 401
    assert client.get("/admin/").status_code == 302


def test_admin_login_requires_csrf(client):
    res = client.post("/admin/login", data={"username": "admin", "password": "correct-horse-battery"})
    assert res.status_code == 400


def test_admin_sees_submissions_and_can_logout(client):
    _failed_logins.clear()
    client.post("/api/submissions", json={"name": "Grace", "surname": "Hopper"})
    assert _login(client).status_code == 302
    html = client.get("/admin/").get_data(as_text=True)
    assert "Grace" in html and "Hopper" in html
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    assert client.post("/admin/logout", data={"csrf_token": token}).status_code == 302
    assert client.get("/admin/").status_code == 302


def test_login_rate_limited(client):
    _failed_logins.clear()
    for _ in range(5):
        _login(client, "wrong")
    assert _login(client).status_code == 429
    _failed_logins.clear()

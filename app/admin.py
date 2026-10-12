import hmac
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash

from .extensions import db
from .models import Submission

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

PER_PAGE = 25
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60
_failed_logins = defaultdict(deque)


def _csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def _check_csrf():
    sent = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not sent or not expected or not hmac.compare_digest(sent, expected):
        abort(400, "Invalid or missing CSRF token.")


@admin_bp.app_context_processor
def inject_csrf():
    return {"csrf_token": _csrf_token}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _verify_credentials(username, password):
    cfg = current_app.config
    expected_user = cfg.get("ADMIN_USERNAME") or ""
    user_ok = hmac.compare_digest(username.encode(), expected_user.encode())
    if cfg.get("ADMIN_PASSWORD_HASH"):
        pass_ok = check_password_hash(cfg["ADMIN_PASSWORD_HASH"], password)
    elif cfg.get("ADMIN_PASSWORD"):
        pass_ok = hmac.compare_digest(password.encode(), cfg["ADMIN_PASSWORD"].encode())
    else:
        return False  # admin disabled until a password is configured
    return user_ok and pass_ok


def _too_many_attempts(ip):
    attempts = _failed_logins[ip]
    now = time.monotonic()
    while attempts and now - attempts[0] > WINDOW_SECONDS:
        attempts.popleft()
    return len(attempts) >= MAX_ATTEMPTS


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("admin.dashboard"))

    configured = bool(current_app.config.get("ADMIN_PASSWORD_HASH") or current_app.config.get("ADMIN_PASSWORD"))

    if request.method == "POST":
        _check_csrf()
        ip = request.remote_addr or "unknown"
        if _too_many_attempts(ip):
            flash("Too many failed attempts. Please wait a few minutes and try again.", "error")
            return render_template("admin/login.html", configured=configured), 429

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if _verify_credentials(username, password):
            _failed_logins.pop(ip, None)
            session.clear()
            session.permanent = True
            session["is_admin"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/admin") or next_url.startswith("//"):
                next_url = url_for("admin.dashboard")
            return redirect(next_url)

        _failed_logins[ip].append(time.monotonic())
        flash("Incorrect username or password.", "error")
        return render_template("admin/login.html", configured=configured), 401

    return render_template("admin/login.html", configured=configured)


@admin_bp.post("/logout")
@admin_required
def logout():
    _check_csrf()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@admin_required
def dashboard():
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(Submission).order_by(Submission.created_at.desc(), Submission.id.desc()),
        page=page, per_page=PER_PAGE, error_out=False,
    )
    return render_template("admin/dashboard.html", pagination=pagination)


@admin_bp.after_request
def no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response

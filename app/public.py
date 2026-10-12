from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import Submission
from .validation import validate_submission

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def index():
    return render_template("index.html")


@public_bp.post("/api/submissions")
def create_submission():
    if not request.is_json:
        return jsonify(ok=False, message="Unsupported request format."), 415

    data, errors = validate_submission(request.get_json(silent=True))
    if errors:
        return jsonify(ok=False, message="Please check the highlighted fields.", errors=errors), 422

    try:
        db.session.add(Submission(name=data["name"], surname=data["surname"]))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Failed to save submission")
        return jsonify(ok=False, message="We couldn't save your details right now. Please try again."), 500

    # Only a confirmation is returned; never stored records.
    return jsonify(ok=True, message="Thank you! Your details were submitted successfully."), 201


@public_bp.get("/healthz")
def healthz():
    return {"status": "ok"}

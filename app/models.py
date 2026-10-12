from datetime import datetime, timezone

from .extensions import db

NAME_MAX_LENGTH = 100


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(NAME_MAX_LENGTH), nullable=False)
    surname = db.Column(db.String(NAME_MAX_LENGTH), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

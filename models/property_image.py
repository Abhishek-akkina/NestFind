from datetime import datetime

from models.extensions import db


class PropertyImage(db.Model):

    __tablename__ = "property_images"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    property_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "properties.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    image_url = db.Column(
        db.Text,
        nullable=False
    )

    public_id = db.Column(
        db.String(255),
        nullable=False
    )

    is_main = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    property = db.relationship(
        "Property",
        backref=db.backref(
            "images",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<PropertyImage {self.id}>"
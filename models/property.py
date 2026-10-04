from datetime import datetime

from models.extensions import db


class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    purpose = db.Column(
        db.String(20),
        nullable=False
    )

    property_type = db.Column(
        db.String(50),
        nullable=False
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    location = db.Column(
        db.String(150),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    pincode = db.Column(
        db.String(10)
    )

    bedrooms = db.Column(
        db.Integer
    )

    bathrooms = db.Column(
        db.Integer
    )

    area = db.Column(
        db.Integer
    )

    furnishing = db.Column(
        db.String(50)
    )

    parking = db.Column(
        db.Boolean,
        default=False
    )

    description = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(30),
        default="available"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Property {self.title}>"
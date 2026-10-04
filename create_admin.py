from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app, db
from models.admin import Admin


with app.app_context():

    username = input(
        "Enter admin username: "
    ).strip()

    password = getpass(
        "Enter admin password: "
    )

    confirm_password = getpass(
        "Confirm admin password: "
    )

    if password != confirm_password:

        print("Passwords do not match.")

    elif not username:

        print("Username cannot be empty.")

    elif not password:

        print("Password cannot be empty.")

    else:

        existing_admin = Admin.query.filter_by(
            username=username
        ).first()

        if existing_admin:

            print(
                "Admin username already exists."
            )

        else:

            admin = Admin(
                username=username,
                password=generate_password_hash(
                    password
                )
            )

            db.session.add(admin)

            db.session.commit()

            print(
                "Admin created successfully."
            )
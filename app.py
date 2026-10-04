from functools import wraps
import os

import cloudinary
import cloudinary.uploader

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_wtf.csrf import CSRFProtect

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from config import Config
from models.extensions import db


# ============================================================
# CREATE APPLICATION
# ============================================================

def create_app():

    app = Flask(__name__)

    # ========================================================
    # CONFIGURATION
    # ========================================================

    app.config.from_object(Config)

    # Secret key is required
    if not app.config.get("SECRET_KEY"):

        raise RuntimeError(
            "SECRET_KEY is not configured. "
            "Please set SECRET_KEY in your .env file."
        )

    # ========================================================
    # CSRF PROTECTION
    # ========================================================

    csrf = CSRFProtect(app)

    # ========================================================
    # FILE UPLOAD CONFIGURATION
    # ========================================================

    # Maximum total request size
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

    MAX_IMAGES = 5

    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    ALLOWED_IMAGE_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    ALLOWED_IMAGE_MIMETYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    }

    # ========================================================
    # CLOUDINARY CONFIGURATION
    # ========================================================

    cloudinary.config(
        cloud_name=app.config.get(
            "CLOUDINARY_CLOUD_NAME"
        ),
        api_key=app.config.get(
            "CLOUDINARY_API_KEY"
        ),
        api_secret=app.config.get(
            "CLOUDINARY_API_SECRET"
        ),
        secure=True
    )

    # ========================================================
    # DATABASE
    # ========================================================

    db.init_app(app)

    # Import models
    from models.property import Property
    from models.property_image import PropertyImage
    from models.admin import Admin
    from models.user import User
    from models.enquiry import Enquiry

    with app.app_context():

        db.create_all()

    # ========================================================
    # HELPER FUNCTIONS
    # ========================================================

    def allowed_image_file(filename):

        if not filename:
            return False

        if "." not in filename:
            return False

        extension = (
            filename.rsplit(".", 1)[1]
            .lower()
        )

        return extension in ALLOWED_IMAGE_EXTENSIONS

    # ========================================================
    # ADMIN REQUIRED DECORATOR
    # ========================================================

    def admin_required(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            admin_id = session.get("admin_id")

            # ------------------------------------------------
            # Check whether admin is logged in
            # ------------------------------------------------

            if not admin_id:

                flash(
                    "Please login as administrator.",
                    "warning"
                )

                return redirect(
                    url_for("admin_login")
                )

            # ------------------------------------------------
            # Verify that the admin account still exists
            # ------------------------------------------------

            admin = Admin.query.get(admin_id)

            if not admin:

                # Clear invalid/stale admin session
                session.clear()

                flash(
                    "Your admin session is no longer valid. "
                    "Please login again.",
                    "warning"
                )

                return redirect(
                    url_for("admin_login")
                )

            return view(*args, **kwargs)

        return wrapped_view

    # ========================================================
    # CUSTOMER LOGIN REQUIRED DECORATOR
    # ========================================================

    def login_required(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            if "user_id" not in session:

                flash(
                    "Please login to continue.",
                    "warning"
                )

                return redirect(
                    url_for("login")
                )

            return view(*args, **kwargs)

        return wrapped_view

    # ========================================================
    # HOME
    # ========================================================

    @app.route("/")
    def home():

        properties = (
            Property.query
            .filter_by(
                status="available"
            )
            .order_by(
                Property.created_at.desc()
            )
            .limit(6)
            .all()
        )

        return render_template(
            "index.html",
            properties=properties
        )

    # ========================================================
    # PROPERTY SEARCH / LISTING
    # ========================================================

    @app.route("/properties")
    def properties():

        query = Property.query.filter_by(
            status="available"
        )

        purpose = request.args.get(
            "purpose",
            ""
        ).strip().lower()

        location = request.args.get(
            "location",
            ""
        ).strip()

        property_type = request.args.get(
            "property_type",
            ""
        ).strip()

        min_price = request.args.get(
            "min_price",
            ""
        ).strip()

        max_price = request.args.get(
            "max_price",
            ""
        ).strip()

        bedrooms = request.args.get(
            "bedrooms",
            ""
        ).strip()

        bathrooms = request.args.get(
            "bathrooms",
            ""
        ).strip()

        furnishing = request.args.get(
            "furnishing",
            ""
        ).strip()

        parking = request.args.get(
            "parking",
            ""
        ).strip()

        if purpose in {"rent", "sale"}:

            query = query.filter(
                Property.purpose == purpose
            )

        if location:

            query = query.filter(
                Property.location.ilike(
                    f"%{location}%"
                )
            )

        if property_type:

            query = query.filter(
                Property.property_type
                == property_type
            )

        if min_price:

            try:

                query = query.filter(
                    Property.price
                    >= float(min_price)
                )

            except ValueError:
                pass

        if max_price:

            try:

                query = query.filter(
                    Property.price
                    <= float(max_price)
                )

            except ValueError:
                pass

        if bedrooms:

            try:

                query = query.filter(
                    Property.bedrooms
                    >= int(bedrooms)
                )

            except ValueError:
                pass

        if bathrooms:

            try:

                query = query.filter(
                    Property.bathrooms
                    >= int(bathrooms)
                )

            except ValueError:
                pass

        if furnishing:

            query = query.filter(
                Property.furnishing
                == furnishing
            )

        if parking == "yes":

            query = query.filter(
                Property.parking.is_(True)
            )

        properties = (
            query
            .order_by(
                Property.created_at.desc()
            )
            .all()
        )

        return render_template(
            "properties.html",
            properties=properties
        )

    # ========================================================
    # PROPERTY DETAILS
    # ========================================================

    @app.route(
        "/property/<int:property_id>"
    )
    def property_details(property_id):

        property = (
            Property.query
            .filter_by(
                id=property_id,
                status="available"
            )
            .first_or_404()
        )

        return render_template(
            "property_details.html",
            property=property
        )

    # ========================================================
    # CUSTOMER REGISTER
    # ========================================================

    @app.route(
        "/register",
        methods=["GET", "POST"]
    )
    def register():

        if "user_id" in session:

            return redirect(
                url_for("dashboard")
            )

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            password = request.form.get(
                "password",
                ""
            )

            confirm_password = request.form.get(
                "confirm_password",
                ""
            )

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            # ----------------------------
            # Validation
            # ----------------------------

            if not name:

                flash(
                    "Name is required.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            if not email:

                flash(
                    "Email is required.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            if not password:

                flash(
                    "Password is required.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            if len(password) < 6:

                flash(
                    "Password must be at least 6 characters.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            if password != confirm_password:

                flash(
                    "Passwords do not match.",
                    "danger"
                )

                return redirect(
                    url_for("register")
                )

            existing_user = User.query.filter_by(
                email=email
            ).first()

            if existing_user:

                flash(
                    "An account with this email already exists.",
                    "danger"
                )

                return redirect(
                    url_for("login")
                )

            # ----------------------------
            # Create user
            # ----------------------------

            user = User(
                name=name,
                email=email,
                password=generate_password_hash(
                    password
                ),
                phone=phone,
                is_active=True
            )

            db.session.add(user)

            db.session.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        return render_template(
            "register.html"
        )

    # ========================================================
    # CUSTOMER LOGIN
    # ========================================================

    @app.route(
        "/login",
        methods=["GET", "POST"]
    )
    def login():

        if "user_id" in session:

            return redirect(
                url_for("dashboard")
            )

        if request.method == "POST":

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            password = request.form.get(
                "password",
                ""
            )

            user = User.query.filter_by(
                email=email
            ).first()

            if (
                user
                and user.is_active
                and check_password_hash(
                    user.password,
                    password
                )
            ):

                # Remove previous session values
                session.clear()

                session["user_id"] = user.id
                session["user_name"] = user.name
                session["user_email"] = user.email

                flash(
                    "Login successful.",
                    "success"
                )

                next_page = request.args.get(
                    "next"
                )

                # Only allow safe internal redirects
                if (
                    next_page
                    and next_page.startswith("/")
                    and not next_page.startswith("//")
                ):

                    return redirect(next_page)

                return redirect(
                    url_for("dashboard")
                )

            flash(
                "Invalid email or password.",
                "danger"
            )

        return render_template(
            "login.html"
        )

    # ========================================================
    # CUSTOMER LOGOUT
    # ========================================================

    @app.route("/logout")
    def logout():

        session.clear()

        flash(
            "You have been logged out.",
            "success"
        )

        return redirect(
            url_for("home")
        )

    # ========================================================
    # CUSTOMER DASHBOARD
    # ========================================================

    @app.route("/dashboard")
    @login_required
    def dashboard():

        user = User.query.get_or_404(
            session["user_id"]
        )

        enquiries = (
            Enquiry.query
            .filter_by(
                user_id=user.id
            )
            .order_by(
                Enquiry.created_at.desc()
            )
            .all()
        )

        return render_template(
            "dashboard.html",
            user=user,
            enquiries=enquiries
        )

    # ========================================================
    # CUSTOMER PROPERTY ENQUIRY
    # ========================================================

    @app.route(
        "/property/<int:property_id>/enquiry",
        methods=["POST"]
    )
    @login_required
    def property_enquiry(property_id):

        property = (
            Property.query
            .filter_by(
                id=property_id,
                status="available"
            )
            .first_or_404()
        )

        user = User.query.get_or_404(
            session["user_id"]
        )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        # ----------------------------
        # Validation
        # ----------------------------

        if not name:

            flash(
                "Name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "property_details",
                    property_id=property.id
                )
            )

        if not email:

            flash(
                "Email is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "property_details",
                    property_id=property.id
                )
            )

        if not phone:

            flash(
                "Phone number is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "property_details",
                    property_id=property.id
                )
            )

        if not message:

            flash(
                "Message is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "property_details",
                    property_id=property.id
                )
            )

        enquiry = Enquiry(
            user_id=user.id,
            property_id=property.id,
            name=name,
            email=email,
            phone=phone,
            message=message,
            status="new"
        )

        db.session.add(enquiry)

        db.session.commit()

        flash(
            "Your enquiry has been submitted successfully!",
            "success"
        )

        return redirect(
            url_for(
                "property_details",
                property_id=property.id
            )
        )

    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    @app.route(
        "/admin/login",
        methods=["GET", "POST"]
    )
    def admin_login():

        if "admin_id" in session:

            return redirect(
                url_for("admin_dashboard")
            )

        if request.method == "POST":

            username = request.form.get(
                "username",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )

            admin = Admin.query.filter_by(
                username=username
            ).first()

            if (
                admin
                and check_password_hash(
                    admin.password,
                    password
                )
            ):

                session.clear()

                session["admin_id"] = admin.id
                session["admin_username"] = (
                    admin.username
                )

                flash(
                    "Admin login successful.",
                    "success"
                )

                return redirect(
                    url_for("admin_dashboard")
                )

            flash(
                "Invalid username or password.",
                "danger"
            )

        return render_template(
            "admin/login.html"
        )

    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    @app.route("/admin/dashboard")
    @admin_required
    def admin_dashboard():

        properties_count = (
            Property.query.count()
        )

        available_count = (
            Property.query
            .filter_by(
                status="available"
            )
            .count()
        )

        rent_count = (
            Property.query
            .filter_by(
                purpose="rent"
            )
            .count()
        )

        sale_count = (
            Property.query
            .filter_by(
                purpose="sale"
            )
            .count()
        )

        users_count = User.query.count()

        enquiries_count = (
            Enquiry.query.count()
        )

        new_enquiries_count = (
            Enquiry.query
            .filter_by(
                status="new"
            )
            .count()
        )

        images_count = (
            PropertyImage.query.count()
        )

        return render_template(
            "admin/dashboard.html",
            properties_count=properties_count,
            available_count=available_count,
            rent_count=rent_count,
            sale_count=sale_count,
            users_count=users_count,
            enquiries_count=enquiries_count,
            new_enquiries_count=new_enquiries_count,
            images_count=images_count
        )

    # ========================================================
    # ADMIN - ADD PROPERTY
    # ========================================================

    @app.route(
        "/admin/properties/add",
        methods=["GET", "POST"]
    )
    @admin_required
    def admin_add_property():

        if request.method == "POST":

            # ----------------------------
            # Form values
            # ----------------------------

            title = request.form.get(
                "title",
                ""
            ).strip()

            purpose = request.form.get(
                "purpose",
                ""
            ).strip().lower()

            property_type = request.form.get(
                "property_type",
                ""
            ).strip()

            price = request.form.get(
                "price",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            address = request.form.get(
                "address",
                ""
            ).strip()

            pincode = request.form.get(
                "pincode",
                ""
            ).strip()

            bedrooms = request.form.get(
                "bedrooms",
                ""
            ).strip()

            bathrooms = request.form.get(
                "bathrooms",
                ""
            ).strip()

            area = request.form.get(
                "area",
                ""
            ).strip()

            furnishing = request.form.get(
                "furnishing",
                ""
            ).strip()

            parking = request.form.get(
                "parking"
            )

            description = request.form.get(
                "description",
                ""
            ).strip()

            status = request.form.get(
                "status",
                "available"
            ).strip().lower()

            images = request.files.getlist(
                "images"
            )

            # Remove empty file objects
            images = [
                image
                for image in images
                if image and image.filename
            ]

            # ----------------------------
            # Basic validation
            # ----------------------------

            if not title:

                flash(
                    "Property title is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            if purpose not in {
                "rent",
                "sale"
            }:

                flash(
                    "Please select Rent or Sale.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            if not property_type:

                flash(
                    "Property type is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            if not price:

                flash(
                    "Price is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            if not location:

                flash(
                    "Location is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            if not address:

                flash(
                    "Address is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            # ----------------------------
            # Image count validation
            # ----------------------------

            if len(images) > MAX_IMAGES:

                flash(
                    "You can upload a maximum of 5 images.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            # ----------------------------
            # Numeric validation
            # ----------------------------

            try:

                price = float(price)

                if price < 0:

                    raise ValueError

                bedrooms = (
                    int(bedrooms)
                    if bedrooms
                    else None
                )

                bathrooms = (
                    int(bathrooms)
                    if bathrooms
                    else None
                )

                area = (
                    int(area)
                    if area
                    else None
                )

                if bedrooms is not None and bedrooms < 0:
                    raise ValueError

                if bathrooms is not None and bathrooms < 0:
                    raise ValueError

                if area is not None and area < 0:
                    raise ValueError

            except ValueError:

                flash(
                    "Please enter valid numeric values.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            # ----------------------------
            # Validate images
            # ----------------------------

            for image in images:

                filename = image.filename

                if not allowed_image_file(
                    filename
                ):

                    flash(
                        f"Invalid image format: {filename}. "
                        "Allowed formats: JPG, JPEG, PNG, WEBP.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_add_property"
                        )
                    )

                mimetype = (
                    image.mimetype
                    or ""
                ).lower()

                if mimetype not in ALLOWED_IMAGE_MIMETYPES:

                    flash(
                        f"Invalid image type: {filename}.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_add_property"
                        )
                    )

                image.seek(
                    0,
                    os.SEEK_END
                )

                image_size = image.tell()

                image.seek(0)

                if image_size <= 0:

                    flash(
                        f"{filename} is empty.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_add_property"
                        )
                    )

                if image_size > MAX_IMAGE_SIZE:

                    flash(
                        f"{filename} is larger than 5 MB.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_add_property"
                        )
                    )

            # ----------------------------
            # Create property
            # ----------------------------

            new_property = Property(

                title=title,

                purpose=purpose,

                property_type=property_type,

                price=price,

                location=location,

                address=address,

                pincode=pincode,

                bedrooms=bedrooms,

                bathrooms=bathrooms,

                area=area,

                furnishing=furnishing,

                parking=True if parking else False,

                description=description,

                status=status

            )

            db.session.add(
                new_property
            )

            db.session.flush()

            uploaded_public_ids = []

            try:

                # ------------------------
                # Upload images
                # ------------------------

                for index, image in enumerate(
                    images
                ):

                    upload_result = (
                        cloudinary.uploader.upload(
                            image,
                            folder="nestfind/properties",
                            resource_type="image"
                        )
                    )

                    image_url = upload_result.get(
                        "secure_url"
                    )

                    public_id = upload_result.get(
                        "public_id"
                    )

                    if not image_url or not public_id:

                        raise RuntimeError(
                            "Cloudinary upload failed."
                        )

                    uploaded_public_ids.append(
                        public_id
                    )

                    property_image = PropertyImage(

                        property_id=new_property.id,

                        image_url=image_url,

                        public_id=public_id,

                        is_main=(
                            True
                            if index == 0
                            else False
                        )

                    )

                    db.session.add(
                        property_image
                    )

                db.session.commit()

            except Exception as error:

                db.session.rollback()

                # Remove already uploaded images
                for public_id in uploaded_public_ids:

                    try:

                        cloudinary.uploader.destroy(
                            public_id,
                            resource_type="image"
                        )

                    except Exception:
                        pass

                print(
                    "Property upload error:",
                    error
                )

                flash(
                    "Property could not be added. "
                    "Please check the image upload settings.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_add_property"
                    )
                )

            flash(
                "Property added successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "admin_edit_property",
                    property_id=new_property.id
                )
            )

        return render_template(
            "admin/add_property.html"
        )

    # ========================================================
    # ADMIN - MANAGE PROPERTIES
    # ========================================================

    @app.route(
        "/admin/properties"
    )
    @admin_required
    def admin_properties():

        properties = (
            Property.query
            .order_by(
                Property.created_at.desc()
            )
            .all()
        )

        return render_template(
            "admin/properties.html",
            properties=properties
        )

    # ========================================================
    # ADMIN - EDIT PROPERTY
    # ========================================================

    @app.route(
        "/admin/properties/edit/<int:property_id>",
        methods=["GET", "POST"]
    )
    @admin_required
    def admin_edit_property(property_id):

        property = Property.query.get_or_404(
            property_id
        )

        if request.method == "POST":

            title = request.form.get(
                "title",
                ""
            ).strip()

            purpose = request.form.get(
                "purpose",
                ""
            ).strip().lower()

            property_type = request.form.get(
                "property_type",
                ""
            ).strip()

            price = request.form.get(
                "price",
                ""
            ).strip()

            location = request.form.get(
                "location",
                ""
            ).strip()

            address = request.form.get(
                "address",
                ""
            ).strip()

            pincode = request.form.get(
                "pincode",
                ""
            ).strip()

            bedrooms = request.form.get(
                "bedrooms",
                ""
            ).strip()

            bathrooms = request.form.get(
                "bathrooms",
                ""
            ).strip()

            area = request.form.get(
                "area",
                ""
            ).strip()

            furnishing = request.form.get(
                "furnishing",
                ""
            ).strip()

            parking = request.form.get(
                "parking"
            )

            description = request.form.get(
                "description",
                ""
            ).strip()

            status = request.form.get(
                "status",
                "available"
            ).strip().lower()

            # ----------------------------
            # Validation
            # ----------------------------

            if not title:

                flash(
                    "Property title is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            if purpose not in {
                "rent",
                "sale"
            }:

                flash(
                    "Please select Rent or Sale.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            if not property_type:

                flash(
                    "Property type is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            if not price:

                flash(
                    "Price is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            if not location:

                flash(
                    "Location is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            if not address:

                flash(
                    "Address is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            try:

                price = float(price)

                if price < 0:
                    raise ValueError

                bedrooms = (
                    int(bedrooms)
                    if bedrooms
                    else None
                )

                bathrooms = (
                    int(bathrooms)
                    if bathrooms
                    else None
                )

                area = (
                    int(area)
                    if area
                    else None
                )

                if bedrooms is not None and bedrooms < 0:
                    raise ValueError

                if bathrooms is not None and bathrooms < 0:
                    raise ValueError

                if area is not None and area < 0:
                    raise ValueError

            except ValueError:

                flash(
                    "Please enter valid numeric values.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_property",
                        property_id=property.id
                    )
                )

            # ----------------------------
            # Update property
            # ----------------------------

            property.title = title
            property.purpose = purpose
            property.property_type = property_type
            property.price = price
            property.location = location
            property.address = address
            property.pincode = pincode
            property.bedrooms = bedrooms
            property.bathrooms = bathrooms
            property.area = area
            property.furnishing = furnishing
            property.parking = (
                True if parking else False
            )
            property.description = description
            property.status = status

            # ----------------------------
            # Optional new image
            # ----------------------------

            new_images = request.files.getlist(
                "images"
            )

            new_images = [
                image
                for image in new_images
                if image and image.filename
            ]

            if new_images:

                if len(new_images) > MAX_IMAGES:

                    flash(
                        "You can upload a maximum of 5 images at a time.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_edit_property",
                            property_id=property.id
                        )
                    )

                for image in new_images:

                    filename = image.filename

                    if not allowed_image_file(
                        filename
                    ):

                        flash(
                            f"Invalid image format: {filename}.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin_edit_property",
                                property_id=property.id
                            )
                        )

                    mimetype = (
                        image.mimetype
                        or ""
                    ).lower()

                    if mimetype not in ALLOWED_IMAGE_MIMETYPES:

                        flash(
                            f"Invalid image type: {filename}.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin_edit_property",
                                property_id=property.id
                            )
                        )

                    image.seek(
                        0,
                        os.SEEK_END
                    )

                    image_size = image.tell()

                    image.seek(0)

                    if image_size <= 0:

                        flash(
                            f"{filename} is empty.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin_edit_property",
                                property_id=property.id
                            )
                        )

                    if image_size > MAX_IMAGE_SIZE:

                        flash(
                            f"{filename} is larger than 5 MB.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin_edit_property",
                                property_id=property.id
                            )
                        )

                uploaded_ids = []

                try:

                    existing_images = (
                        PropertyImage.query
                        .filter_by(
                            property_id=property.id
                        )
                        .count()
                    )

                    if (
                        existing_images
                        + len(new_images)
                        > MAX_IMAGES
                    ):

                        flash(
                            "A property can have a maximum of 5 images.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin_edit_property",
                                property_id=property.id
                            )
                        )

                    for image in new_images:

                        upload_result = (
                            cloudinary.uploader.upload(
                                image,
                                folder="nestfind/properties",
                                resource_type="image"
                            )
                        )

                        image_url = upload_result.get(
                            "secure_url"
                        )

                        public_id = upload_result.get(
                            "public_id"
                        )

                        if not image_url or not public_id:

                            raise RuntimeError(
                                "Cloudinary upload failed."
                            )

                        uploaded_ids.append(
                            public_id
                        )

                        has_existing_main = (
                            PropertyImage.query
                            .filter_by(
                                property_id=property.id
                            )
                            .count()
                            > 0
                        )

                        new_property_image = PropertyImage(

                            property_id=property.id,

                            image_url=image_url,

                            public_id=public_id,

                            is_main=(
                                not has_existing_main
                            )

                        )

                        db.session.add(
                            new_property_image
                        )

                    db.session.commit()

                except Exception as error:

                    db.session.rollback()

                    for public_id in uploaded_ids:

                        try:

                            cloudinary.uploader.destroy(
                                public_id,
                                resource_type="image"
                            )

                        except Exception:
                            pass

                    print(
                        "Edit image upload error:",
                        error
                    )

                    flash(
                        "New image upload failed.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin_edit_property",
                            property_id=property.id
                        )
                    )

            else:

                db.session.commit()

            flash(
                "Property updated successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "admin_edit_property",
                    property_id=property.id
                )
            )

        return render_template(
            "admin/edit_property.html",
            property=property
        )

    # ========================================================
    # ADMIN - SET MAIN IMAGE
    # ========================================================

    @app.route(
        "/admin/properties/<int:property_id>/images/<int:image_id>/main",
        methods=["POST"]
    )
    @admin_required
    def admin_set_main_image(
        property_id,
        image_id
    ):

        property = Property.query.get_or_404(
            property_id
        )

        image = (
            PropertyImage.query
            .filter_by(
                id=image_id,
                property_id=property.id
            )
            .first_or_404()
        )

        # Remove main status from all images
        PropertyImage.query.filter_by(
            property_id=property.id
        ).update(
            {
                "is_main": False
            }
        )

        image.is_main = True

        db.session.commit()

        flash(
            "Main image updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "admin_edit_property",
                property_id=property.id
            )
        )

    # ========================================================
    # ADMIN - DELETE PROPERTY IMAGE
    # ========================================================

    @app.route(
        "/admin/properties/<int:property_id>/images/<int:image_id>/delete",
        methods=["POST"]
    )
    @admin_required
    def admin_delete_property_image(
        property_id,
        image_id
    ):

        property = Property.query.get_or_404(
            property_id
        )

        image = (
            PropertyImage.query
            .filter_by(
                id=image_id,
                property_id=property.id
            )
            .first_or_404()
        )

        was_main = image.is_main

        public_id = image.public_id

        # Delete from Cloudinary
        if public_id:

            try:

                cloudinary.uploader.destroy(
                    public_id,
                    resource_type="image"
                )

            except Exception as error:

                print(
                    "Cloudinary delete error:",
                    error
                )

        db.session.delete(
            image
        )

        db.session.commit()

        # If deleted image was main,
        # make the earliest remaining image main
        if was_main:

            remaining_image = (
                PropertyImage.query
                .filter_by(
                    property_id=property.id
                )
                .order_by(
                    PropertyImage.created_at.asc()
                )
                .first()
            )

            if remaining_image:

                remaining_image.is_main = True

                db.session.commit()

        flash(
            "Property image deleted successfully!",
            "success"
        )

        return redirect(
            url_for(
                "admin_edit_property",
                property_id=property.id
            )
        )

    # ========================================================
    # ADMIN - DELETE PROPERTY
    # ========================================================

    @app.route(
        "/admin/properties/delete/<int:property_id>",
        methods=["POST"]
    )
    @admin_required
    def admin_delete_property(property_id):

        property = Property.query.get_or_404(
            property_id
        )

        # Delete Cloudinary images first
        images = (
            PropertyImage.query
            .filter_by(
                property_id=property.id
            )
            .all()
        )

        for image in images:

            if image.public_id:

                try:

                    cloudinary.uploader.destroy(
                        image.public_id,
                        resource_type="image"
                    )

                except Exception as error:

                    print(
                        "Cloudinary delete error:",
                        error
                    )

        db.session.delete(
            property
        )

        db.session.commit()

        flash(
            "Property deleted successfully!",
            "success"
        )

        return redirect(
            url_for("admin_properties")
        )

    # ========================================================
    # ADMIN - ENQUIRIES
    # ========================================================

    @app.route(
        "/admin/enquiries"
    )
    @admin_required
    def admin_enquiries():

        enquiries = (
            Enquiry.query
            .order_by(
                Enquiry.created_at.desc()
            )
            .all()
        )

        return render_template(
            "admin/enquiries.html",
            enquiries=enquiries
        )

    # ========================================================
    # ADMIN - UPDATE ENQUIRY STATUS
    # ========================================================

    @app.route(
        "/admin/enquiries/<int:enquiry_id>/status",
        methods=["POST"]
    )
    @admin_required
    def admin_update_enquiry_status(
        enquiry_id
    ):

        enquiry = Enquiry.query.get_or_404(
            enquiry_id
        )

        status = request.form.get(
            "status",
            ""
        ).strip().lower()

        allowed_statuses = {
            "new",
            "contacted",
            "closed"
        }

        if status not in allowed_statuses:

            flash(
                "Invalid enquiry status.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_enquiries"
                )
            )

        enquiry.status = status

        db.session.commit()

        flash(
            "Enquiry status updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "admin_enquiries"
            )
        )

    # ========================================================
    # ADMIN - USERS
    # ========================================================

    @app.route(
        "/admin/users"
    )
    @admin_required
    def admin_users():

        users = (
            User.query
            .order_by(
                User.created_at.desc()
            )
            .all()
        )

        return render_template(
            "admin/users.html",
            users=users
        )

    # ========================================================
    # ADMIN - TOGGLE USER STATUS
    # ========================================================

    @app.route(
        "/admin/users/<int:user_id>/toggle",
        methods=["POST"]
    )
    @admin_required
    def admin_toggle_user(
        user_id
    ):

        user = User.query.get_or_404(
            user_id
        )

        user.is_active = not user.is_active

        db.session.commit()

        flash(
            "User status updated successfully!",
            "success"
        )

        return redirect(
            url_for("admin_users")
        )

    # ========================================================
    # ADMIN LOGOUT
    # ========================================================

    @app.route(
        "/admin/logout",
        methods=["POST"]
    )
    def admin_logout():

        session.clear()

        flash(
            "You have been logged out.",
            "success"
        )

        return redirect(
            url_for("admin_login")
        )

    # ========================================================
    # CSRF ERROR HANDLER
    # ========================================================

    @app.errorhandler(413)
    def request_entity_too_large(error):

        flash(
            "Uploaded files are too large. "
            "Please keep the total upload below 32 MB.",
            "danger"
        )

        return redirect(
            url_for("admin_add_property")
        )

    # ========================================================
    # RETURN APPLICATION
    # ========================================================

    return app


# ============================================================
# CREATE APPLICATION
# ============================================================

app = create_app()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=app.config.get(
            "DEBUG",
            False
        )
    )
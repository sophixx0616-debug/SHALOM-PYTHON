"""Database models (ported from the Spring Boot entity classes)."""

from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

STAMPS_PER_REWARD = 9


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return self.name


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    google_id = db.Column(db.String(255))
    photo_url = db.Column(db.String(500))
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    role = db.relationship("Role", back_populates="users")
    loyalty_card = db.relationship(
        "LoyaltyCard",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    appointments = db.relationship("Appointment", back_populates="user")

    # -- password helpers -------------------------------------------------
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    # -- role helpers -----------------------------------------------------
    @property
    def is_admin(self):
        return self.role is not None and (self.role.name or "").lower() == "admin"

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.name} {self.last_name}"
        return self.name or ""

    @property
    def display_name(self):
        return self.name or self.email or ""

    def __repr__(self):
        return self.email


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    duration = db.Column(db.Integer)
    status = db.Column(db.Boolean, nullable=False, default=True)
    image = db.Column(db.String(500))
    category = db.Column(db.String(255))

    appointments = db.relationship("Appointment", back_populates="service")

    def __repr__(self):
        return self.name


class Specialist(db.Model):
    __tablename__ = "specialists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(500))

    def __repr__(self):
        return self.name


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pendiente")
    worker = db.Column(db.String(255))
    loyalty_stamped_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="appointments")
    service = db.relationship("Service", back_populates="appointments")

    @property
    def end_time(self):
        minutes = self.service.duration if self.service and self.service.duration and self.service.duration > 0 else 30
        return (datetime.combine(self.date, self.time) + timedelta(minutes=minutes)).time()

    def __repr__(self):
        return f"{self.date} {self.time}"


class Inventory(db.Model):
    __tablename__ = "inventories"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(255))
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=False, default=5)
    category = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    image = db.Column(db.String(500))

    movements = db.relationship("InventoryMovement", back_populates="product")

    @property
    def low_stock(self):
        return self.stock <= self.min_stock

    def __repr__(self):
        return self.product_name


class InventoryMovement(db.Model):
    __tablename__ = "inventory_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("inventories.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    stock_before = db.Column(db.Integer, default=0)
    stock_after = db.Column(db.Integer, default=0)
    reason = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    product = db.relationship("Inventory", back_populates="movements")
    user = db.relationship("User")

    def __repr__(self):
        return f"{self.type} {self.quantity}"


class LoyaltyCard(db.Model):
    __tablename__ = "loyalty_cards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    stamps = db.Column(db.Integer, nullable=False, default=0)
    available_rewards = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", back_populates="loyalty_card")

    def add_stamp(self):
        self.stamps += 1
        if self.stamps >= STAMPS_PER_REWARD:
            self.stamps = 0
            self.available_rewards += 1

    def __repr__(self):
        return f"card(user={self.user_id}, stamps={self.stamps})"


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

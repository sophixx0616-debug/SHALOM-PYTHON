"""Database initialisation: roles, the admin account and the service catalog.

Ported from com.shalom.config.DataInitializer.
"""

from .extensions import db
from .models import Role, Service, User
from .seed_services import SERVICES

ADMIN_EMAIL = "admin@shalom.com"
ADMIN_PASSWORD = "admin123"


def seed_database():
    """Idempotent seed, mirroring the Spring CommandLineRunner."""
    admin_role = Role.query.filter_by(name="ADMIN").first()
    if admin_role is None:
        admin_role = Role(name="ADMIN")
        db.session.add(admin_role)

    client_role = Role.query.filter_by(name="CLIENTE").first()
    if client_role is None:
        client_role = Role(name="CLIENTE")
        db.session.add(client_role)

    db.session.flush()

    if User.query.filter_by(email=ADMIN_EMAIL).first() is None:
        admin = User(name="Administrador", email=ADMIN_EMAIL, role=admin_role, enabled=True)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)

    if Service.query.count() == 0:
        for item in SERVICES:
            db.session.add(Service(**item))

    db.session.commit()


def reset_database():
    db.drop_all()
    db.create_all()
    seed_database()

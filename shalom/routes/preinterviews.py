"""Administrator inbox for hiring pre-interviews."""

from flask import Blueprint, abort, flash, redirect, render_template, request

from ..decorators import admin_required
from ..extensions import db
from ..models import PreInterview

bp = Blueprint("preinterviews", __name__, url_prefix="/preentrevistas")

VALID_STATUSES = {"pendiente", "contactar", "no_seleccionado"}


@bp.get("")
@admin_required
def index():
    applications = PreInterview.query.order_by(PreInterview.created_at.desc()).all()
    return render_template("loyalty/preinterviews/index.html", applications=applications)


@bp.post("/<int:application_id>/status")
@admin_required
def update_status(application_id):
    application = db.session.get(PreInterview, application_id)
    if application is None:
        abort(404)

    status = request.form.get("status", "")
    if status not in VALID_STATUSES:
        flash("Selecciona un estado válido para la postulación.", "error")
        return redirect("/preentrevistas")

    application.status = status
    db.session.commit()
    flash("Estado de la postulación actualizado.", "success")
    return redirect("/preentrevistas")

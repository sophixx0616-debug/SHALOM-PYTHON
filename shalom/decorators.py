"""Shared access-control decorators."""

from functools import wraps

from flask import abort, redirect
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect("/login")
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped

from flask import Blueprint

bp = Blueprint("io", __name__, url_prefix="/io")

from . import routes  # noqa: E402, F401

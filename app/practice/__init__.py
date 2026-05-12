from flask import Blueprint

bp = Blueprint("practice", __name__, url_prefix="/practice")

from . import routes  # noqa: E402, F401

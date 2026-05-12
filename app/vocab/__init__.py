from flask import Blueprint

bp = Blueprint("vocab", __name__, url_prefix="/vocab")

from . import routes  # noqa: E402, F401

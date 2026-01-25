from flask import Blueprint

user_bp = Blueprint('users', __name__)
internal_bp = Blueprint('internal', __name__)

from app.routes.user_routes import *
from app.routes.internal_routes import *

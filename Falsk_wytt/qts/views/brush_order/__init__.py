from flask import Blueprint

brushOrder_blue = Blueprint('brushOrder_blue', __name__, url_prefix='/brushOrder')

from . import views
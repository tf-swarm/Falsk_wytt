from flask import Blueprint

dampingOrder_blue = Blueprint('dampingOrder_blue', __name__, url_prefix='/dampingOrder')

from . import views
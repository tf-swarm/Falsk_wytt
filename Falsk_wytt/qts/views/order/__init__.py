from flask import Blueprint

order_blue = Blueprint('order_blue',__name__, url_prefix='/order')

from . import views
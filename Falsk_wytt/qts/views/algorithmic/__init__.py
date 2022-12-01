from flask import Blueprint

TWAP_blue = Blueprint('TWAP_blue', __name__, url_prefix='/TWAP')

from . import views
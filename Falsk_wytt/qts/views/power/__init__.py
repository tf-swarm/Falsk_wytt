from flask import Blueprint

power_blue = Blueprint('Power_blue', __name__, url_prefix='/rights')

from . import views
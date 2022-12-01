from flask import Blueprint

analyze_blue = Blueprint('analyze_blue', __name__, url_prefix='/analyze')

from . import views
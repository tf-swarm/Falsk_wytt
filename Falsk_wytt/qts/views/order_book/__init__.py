from flask import Blueprint

orderBook_blue = Blueprint('orderBook_blue', __name__, url_prefix='/orderBook')

from . import views
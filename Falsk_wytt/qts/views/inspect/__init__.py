from flask import Blueprint

index_blue = Blueprint('index_blue', __name__, url_prefix='/indexBlue')
# index_blue = Blueprint('index_blue',__name__)
from . import views
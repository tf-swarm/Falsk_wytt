from flask import Blueprint

user_blue = Blueprint('user_blue', __name__)

from . import views
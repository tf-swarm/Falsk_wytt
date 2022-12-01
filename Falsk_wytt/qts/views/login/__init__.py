from flask import Blueprint

login_blue = Blueprint('login', __name__,)

from . import views
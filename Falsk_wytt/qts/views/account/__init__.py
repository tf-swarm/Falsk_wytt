from flask import Blueprint

account_blue = Blueprint('account_blue', __name__, url_prefix='/account')

from . import views
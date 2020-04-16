from flask import Blueprint

bp = Blueprint('gr_stats', __name__)

from app.gr_stats import routes 
# -*- coding: utf-8 -*-
from flask import Blueprint

blueprint = Blueprint('crons', __name__)

from rcpapp.crons import routes

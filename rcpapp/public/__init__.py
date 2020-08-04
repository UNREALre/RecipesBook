# -*- coding: utf-8 -*-
from flask import Blueprint

blueprint = Blueprint('public', __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/public/static/')

from rcpapp.public.routes import routes

# -*- coding: utf-8 -*-
from flask_babel import Babel
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_mail import Mail

babel = Babel()
db = MongoEngine()
login = LoginManager()
mail = Mail()

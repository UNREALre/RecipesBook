# -*- coding: utf-8 -*-
from flask import Flask, request, session, current_app
from flask_babel import lazy_gettext as _l
from rcpapp.public import blueprint as public_bp
from rcpapp.errors import blueprint as error_bp
from rcpapp.crons import blueprint as cron_bp
from config import Config
from rcpapp.extensions import db, babel, login, mail


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    elif not session.get('lang'):
        session['lang'] = request.accept_languages.best_match(current_app.config['LANGUAGES'])

    return session.get('lang', 'ru')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    babel.init_app(app)
    mail.init_app(app)

    login.init_app(app)
    login.login_view = 'public.login'
    login.login_message = _l('Пожалуйста, авторизуйтесь, чтобы получить доступ к этой странице')

    app.register_blueprint(public_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(cron_bp, url_prefix='/worker')

    return app

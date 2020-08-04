# -*- coding: utf-8 -*-
import os
import confuse

project_root = os.path.dirname(os.path.abspath(__file__))
os.environ['RECIPESDIR'] = project_root
appConfig = confuse.Configuration('RECIPES')


class Config:
    SECRET_KEY = appConfig['app']['secret'].get() or os.urandom(24)
    WORKER_KEY = appConfig['app']['worker'].get()

    RECIPES_PER_PAGE = 20

    LANGUAGES = ['ru', 'en']

    MONGODB_SETTINGS = {
        'db': appConfig['db']['name'].get(),
        'host': appConfig['db']['host'].get(),
        'port': appConfig['db']['port'].get(),
        'username': appConfig['db']['user'].get(),
        'password': appConfig['db']['pass'].get()
    }

    MAIL_SERVER = appConfig['mail']['host'].get()
    MAIL_PORT = int(appConfig['mail']['port'].get() or 25)
    MAIL_USE_TLS = True
    MAIL_USERNAME = appConfig['mail']['user'].get()
    MAIL_PASSWORD = appConfig['mail']['pass'].get()
    ADMINS = ['avpmanager@gmail.com']
    SENDER = appConfig['app']['email'].get()

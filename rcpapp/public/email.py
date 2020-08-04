# -*- coding: utf-8 -*-
from flask import current_app
from flask_mail import Message
from threading import Thread
from rcpapp.extensions import mail


def send_async_email(app, subject, sender, recipients, text_body, html_body):
    with app.app_context():
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    Thread(target=send_async_email,
           args=[current_app._get_current_object(), subject, sender, recipients, text_body, html_body]).start()

# -*- coding: utf-8 -*-
from wtforms.validators import ValidationError
from flask_mongoengine import DoesNotExist
from flask_babel import lazy_gettext as _l
from rcpapp.models import User, PassRecovery
from datetime import datetime


def mail_validator(raise_if_exist=True):
    """Factory, получает флаг наступления ошибки - используется в регистрации, восстановлении пароля"""

    message = \
        _l('Пользователь с таким E-mail уже зарегистрирован в системе') if raise_if_exist else \
        _l('Пользователя с таким E-mail не найдено в системе')

    def validate(form, field):
        try:
            User.objects.get(email=field.data)
        except DoesNotExist:
            if not raise_if_exist:
                raise ValidationError(message)
        else:
            if raise_if_exist:
                raise ValidationError(message)

    return validate


def pass_sent_validator(form, field):
    try:
        user = User.objects.get(email=field.data)
    except DoesNotExist:
        user = None
    else:
        try:
            recovered = PassRecovery.objects.get(user=user)
        except DoesNotExist:
            recovered = None
        else:
            if recovered.expire > datetime.utcnow():
                minutes = (recovered.expire - datetime.utcnow()).seconds // 60
                raise ValidationError(_l('E-mail для восстановления пароля уже был отправлен! '
                                         'Повторная отправка будет возможно через {} мин.'.format(minutes)))
            else:
                recovered.delete()

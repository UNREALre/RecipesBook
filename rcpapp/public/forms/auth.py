# -*- coding: utf-8 -*-
from flask_mongoengine import DoesNotExist
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms import (StringField, PasswordField, BooleanField, TextAreaField, SelectField, SubmitField, HiddenField)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from rcpapp.models import User
from rcpapp.public.validators import mail_validator, pass_sent_validator


class LoginForm(FlaskForm):
    username = StringField(_l('Логин'), validators=[DataRequired()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Запомнить меня'))
    submit = SubmitField(_l('Войти'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Логин'), validators=[DataRequired()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    password2 = PasswordField(_l('Повторите пароль'), validators=[DataRequired(), EqualTo('password')])
    email = StringField(_l('E-mail'), validators=[DataRequired(), Email(), mail_validator()])
    submit = SubmitField(_l('Регистрация'))

    def validate_username(self, login):
        try:
            user = User.objects.get(username=login.data)
        except DoesNotExist:
            ok = True
        else:
            raise ValidationError(_l('Пользователь с таким логином уже зарегистрирован в системе'))


class PasswordRecoveryForm(FlaskForm):
    email = StringField(_l('E-mail, указанный при регистрации'),
                        validators=[DataRequired(), Email(), mail_validator(False), pass_sent_validator])
    submit = SubmitField(_l('Восстановить'))


class PasswordResetForm(FlaskForm):
    password = PasswordField(_l('Новый пароль'), validators=[DataRequired()])
    password2 = PasswordField(_l('Потоврите пароль'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Сменить пароль'))

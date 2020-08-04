# -*- coding: utf-8 -*-
from flask_mongoengine import DoesNotExist
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms import (StringField, PasswordField, BooleanField, TextAreaField,
                     SelectField, SubmitField, HiddenField)
from flask_wtf.file import FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from bson.objectid import ObjectId
from rcpapp.models import Category


class RecipeForm(FlaskForm):
    title = StringField(_l('Название рецепта'), validators=[DataRequired()])
    category = SelectField(_l('Категория'), coerce=ObjectId, validators=[DataRequired()])
    cooking_time = StringField(_l('Время приготовления'), validators=[Optional()])
    difficulty = SelectField(_l('Сложность приготовления'), coerce=int,
                             choices=[(0, _l('Сложность приготовления')), (1, _l('легко')),
                                      (2, _l('средне')), (3, _l('сложно'))],
                             validators=[DataRequired()])
    description = TextAreaField(_l('Описание процесса приготовления'), validators=[DataRequired()])
    picture = FileField(_l('Фото рецепта'), validators=[Optional()])
    is_searchable = BooleanField(_l('Публичный рецепт'))
    submit = SubmitField(_l('Сохранить'))

    def init_data(self):
        self.category.choices = [(category.id, category.name) for category in Category.objects().order_by('+order')]
        self.category.choices.insert(0, (None, _l('Категория')))


class ContactForm(FlaskForm):
    name = StringField(_l('Имя'), validators=[DataRequired()])
    email = StringField(_l('E-mail'), validators=[DataRequired(), Email()])
    message = TextAreaField(_l('Сообщение'), validators=[DataRequired()])
    submit = SubmitField(_l('Отправить'))


class SearchForm(FlaskForm):
    keyword = StringField(_l('Что ищем?'), validators=[DataRequired()])
    category = SelectField(_l('Категория'), coerce=str, validators=[Optional()])
    submit = SubmitField(_l('Начать готовить!'))

    def init_data(self):
        self.category.choices = [(category.name, category.name) for category in Category.objects().order_by('+order')]
        self.category.choices.insert(0, ("None", _l('все категории')))

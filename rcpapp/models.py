# -*- coding: utf-8 -*-
from rcpapp.extensions import db
from flask import current_app
from flask_mongoengine.wtf import model_form
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from mongoengine import EmbeddedDocumentField, EmbeddedDocument
from datetime import datetime, timedelta
from gridfs import GridFS
from mongoengine.fields import get_db
from bson import ObjectId
import re

from rcpapp.extensions import login


class User(UserMixin, db.Document):
    username = db.StringField(max_length=20, required=True, unique=True)
    password_hash = db.StringField(max_length=128, required=True)
    email = db.EmailField(required=True, unique=True)
    telegram_id = db.StringField()
    is_featured = db.BooleanField(defaul=False)
    achievement_list = db.ListField(db.StringField(max_length=100))

    @property
    def achievements(self):
        return [achievement for achievement in self.achievement_list]

    @achievements.setter
    def achievements(self, value):
        if not self.achievements.count(value):
            self.achievement_list.append(value)

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def recipes(self):
        return Recipe.objects(user=self).order_by('-added')

    def favourites(self):
        return Recipe.objects(likes__user=self.id)

    def get_top_recipe(self):
        """Возвращает наиболее залайканный рецепт и его позицию среди прочих рецептов сайта"""

        top_10 = Recipe.objects.aggregate([
            {
                '$project': {
                    'user': '$user',
                    'likes_num': {'$size': '$likes'}
                }
            },
            {
                '$sort': {'likes_num': -1}
            },
            {
                '$limit': 10
            }
        ])
        for idx, recipe in enumerate(top_10):
            if recipe['user'] == self.id and recipe['likes_num']:
                return recipe['_id'], idx+1

        return None, 0


@login.user_loader
def load_user(user_id):
    return User.objects.get(id=user_id)


class PassRecovery(db.Document):
    user = db.ReferenceField(User, required=True)
    recovery_hash = db.StringField(max_length=128, required=True)
    expire = db.DateTimeField(default=datetime.utcnow() + timedelta(minutes=15))

    def __repr__(self):
        return '<PassRecovery: for {} expire {}>'.format(self.user, self.expire)


class Feedback(db.Document):
    user = db.ReferenceField(User, requiired=False)
    name = db.StringField(max_length=100, required=True)
    email = db.EmailField(max_length=100, required=True)
    message = db.StringField(required=True)

    def __repr__(self):
        return '<Feedback: #{} from {}>'.format(self.id, self.name)


class Category(db.Document):
    name = db.StringField(max_length=100, required=True)
    icon = db.StringField(max_length=100, required=True)
    slug = db.StringField(max_length=100, required=True)
    order = db.IntField(default=0)

    def __repr__(self):
        return '<Category: #{}, {}>'.format(self.id, self.name)


class Ingredient(db.Document):
    name = db.StringField(max_length=100, required=True)
    normalized_name = db.StringField(max_length=100, required=False)

    def __repr__(self):
        return '<Ingredient: #{}, {}>'.format(self.id, self.name)

    meta = {
        'indexes': [{
            'fields': ['$name'],
            'default_language': 'russian',
            'weights': {
                'name': 10
            }
        }]
    }


class RecipeIngredient(EmbeddedDocument):
    ingredient = db.ReferenceField(Ingredient, required=True)
    quantity = db.StringField(max_length=100, required=True)

    def __repr__(self):
        return '<RecipeIngredient: #{} - {}>'.format(self.id, self.ingredient)


class RecipeLike(EmbeddedDocument):
    user = db.ReferenceField(User, required=True)
    added = db.DateTimeField(default=datetime.utcnow)


class Recipe(db.Document):
    user = db.ReferenceField(User, required=True)
    category = db.ReferenceField(Category, required=True)
    title = db.StringField(max_length=200, required=True)
    ingredients = db.ListField(EmbeddedDocumentField(RecipeIngredient), required=True)
    description = db.StringField(required=True)
    normalized_description = db.StringField(required=False)
    picture = db.FileField(required=False)
    difficulty = db.IntField(default=1)
    cooking_time = db.StringField(max_length=100, required=False)
    likes = db.ListField(EmbeddedDocumentField(RecipeLike), required=False)
    is_searchable = db.BooleanField(default=True)
    is_featured = db.BooleanField(default=False)
    added = db.DateTimeField(default=datetime.utcnow)
    updated = db.DateTimeField()

    def __repr__(self):
        return '<Recipe: #{} - {}>'.format(self.id, self.title)

    def set_picture(self, user_file):
        self.picture.new_file()
        self.picture.write(user_file.read())
        self.picture.close()

    def get_picture(self):
        db = get_db()
        fs = GridFS(db)
        picture = fs.get(ObjectId(self.picture._id))
        return picture

    def delete_picture(self):
        if self.picture:
            db = get_db()
            fs = GridFS(db)
            fs.delete(ObjectId(self.picture._id))
            self.picture.delete()

    @classmethod
    def search(cls, keyword, category, page):
        search_query = dict()
        search_query['$and'] = []
        search_query['$and'].append({'is_searchable': True})
        search_query['is_searchable'] = True

        if category and category != 'None':
            category = Category.objects.get_or_404(name=category)
            search_query['$and'].append({'category': category.id})

        if (keyword):
            regex = re.compile('.*{}*.'.format(keyword), re.IGNORECASE)
            ingredients = Ingredient.objects(name=regex).distinct(field='id')
            search_query['$and'].append({
                '$or': [
                    {'ingredients.ingredient': {'$in': ingredients}},
                    {'title': regex},
                    {'description': regex}
                ]
            })

        return cls.objects(__raw__=search_query).order_by('-added').\
            paginate(page=page, per_page=current_app.config['RECIPES_PER_PAGE'])

    meta = {
        'indexes': [{
            'fields': ['$title', '$description'],
            'default_language': 'russian',
            'weights': {
                'title': 10,
                'description': 5
            }
        }]
    }

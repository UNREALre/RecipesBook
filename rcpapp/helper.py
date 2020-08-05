# -*- coding: utf-8 -*-
import os
from config import project_root
from flask_mongoengine import DoesNotExist
from rcpapp.models import Ingredient, RecipeIngredient, User
import nltk
import string


def css_js_update_time(target='public'):
    """Возвращает словарь с временем обновлений статики. Если for_public - то обходим паблик статику."""

    if target == 'public':
        static = {
            'public/static/css/custom.css': 0,
            'public/static/js/custom.js': 0,
        }
    else:
        static = {
        }

    for path, time in static.items():
        static[path] = os.path.getmtime(os.path.join(project_root, 'rcpapp/', path))

    return static


def get_recipe_ingredients(rcp_ingredients, rcp_ingredients_qty):
    """Получает из формы список ингредиентов и количеств, возвращает список объектов RecipeIngredient для БД"""

    ingredients = []
    for i in range(len(rcp_ingredients)):
        try:
            ingredient = Ingredient.objects.get(name=rcp_ingredients[i])
        except DoesNotExist:
            normalized = [token for token in tokenize(rcp_ingredients[i])]
            ingredient = Ingredient(name=rcp_ingredients[i].strip(), normalized_name=' '.join(normalized))
            ingredient.save()
        finally:
            recipe_ingredient = RecipeIngredient(ingredient=ingredient, quantity=rcp_ingredients_qty[i])
            ingredients.append(recipe_ingredient)

    return ingredients


def normalize_text(text):
    result = tokenize(text)
    return ' '.join(result)


def tokenize(text):
    """
    Упрощенная лексимизация для хранения нормализованных описания рецепта и ингредиентов для последующего поиска.

    Отбрасывает знаки препинания, используя набор символов string.punctuation.
    Преобразует оставшиеся символы в нижний регистр.
    Сворачивает свойства с помощью SnowballStemmer (по типу удаления суффиксов мн.числа в en и тд)
    Возвращает генератор.
    """

    stem = nltk.stem.SnowballStemmer('russian')
    text = text.lower()

    for token in nltk.word_tokenize(text):
        if token in string.punctuation:
            continue

        yield stem.stem(token)


def add_achievement(name, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.achievements = name
        print(user.achievements)
        user.save()
        return True
    except:
        return False

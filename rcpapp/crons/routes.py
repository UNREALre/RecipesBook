# -*- coding: utf-8 -*-
from flask import (render_template, redirect, request, session, url_for, current_app,
                   flash, make_response, abort, jsonify)
from random import randrange
from mongoengine import DoesNotExist

from rcpapp.crons import blueprint
from rcpapp.models import Recipe, User
from rcpapp.helper import add_achievement


@blueprint.route('/set-daily-recipe')
def set_daily_recipe():
    if not validate_worker():
        abort(403)
    else:
        rand = randrange(0, Recipe.objects(is_searchable=True).count() - 1)
        current_featured = None
        try:
            current_featured = Recipe.objects.get(is_featured=True)
        except:
            current_featured = None
        finally:
            if current_featured:
                new_featured = Recipe.objects(id__ne=current_featured.id, is_searchable=True)[rand:rand+1].first()
            else:
                new_featured = Recipe.objects(is_searchable=True)[rand:rand+1].first()

        Recipe.objects().update(is_featured=False)
        new_featured.is_featured = True
        new_featured.save()

        add_achievement('рецепт на главной', new_featured.user.id)

        return jsonify({"data": "ok"})


@blueprint.route('/set-daily-user')
def set_daily_user():
    if not validate_worker():
        abort(403)
    else:
        rand = randrange(0, User.objects.count() - 1)
        current_featured = None
        try:
            current_featured = User.objects.get(is_featured=True)
        except:
            current_featured = None
        finally:
            if current_featured:
                new_featured = User.objects(id__ne=current_featured.id)[rand:rand+1].first()
            else:
                new_featured = User.objects()[rand:rand+1].first()

        User.objects().update(is_featured=False)
        new_featured.is_featured = True
        new_featured.save()

        return jsonify({"data": "ok"})


def validate_worker():
    return request.args.get('key') == current_app.config['WORKER_KEY']

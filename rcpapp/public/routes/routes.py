# -*- coding: utf-8 -*-
from flask import (render_template, redirect, request, session, url_for, current_app,
                   flash, make_response, abort, jsonify)
from rcpapp.public import blueprint
from flask_babel import lazy_gettext as _l, _
from flask_login import current_user, login_user, login_required
from flask_mongoengine import DoesNotExist, MultipleObjectsReturned
from gridfs.errors import NoFile
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from rcpapp.helper import css_js_update_time, get_recipe_ingredients, normalize_text, add_achievement
from rcpapp.public.routes import auth
from rcpapp.public.forms import RecipeForm, ContactForm, SearchForm
from rcpapp.models import Recipe, Category, User, RecipeLike, Feedback, Ingredient
from rcpapp.public.email import send_email


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
def index():
    times = css_js_update_time()

    form = SearchForm()
    form.init_data()
    if form.validate_on_submit():
        return redirect(url_for('public.search', keyword=form.keyword.data, category=form.category.data))

    categories = Category.objects().order_by('order')
    try:
        featured_recipe = Recipe.objects.get(is_featured=True)
    except DoesNotExist:
        featured_recipe = Recipe.objects().first()
    except MultipleObjectsReturned:
        featured_recipe = Recipe.objects(is_featured=True).first()

    try:
        featured_user = User.objects.get(is_featured=True)
    except DoesNotExist:
        featured_user = User.objects().first()
    except MultipleObjectsReturned:
        featured_user = User.objects(is_featured=True).first()

    top_recipe = Recipe.objects()[:1].order_by('-likes').first()

    recipes = Recipe.objects(is_searchable=True).order_by('-added')[:6]

    latest_user = User.objects().order_by('-id').first()
    top_user = User.objects.get(id=top_recipe.user.id) if top_recipe else latest_user

    return render_template('index.html',
                           form=form,
                           latest_user=latest_user,
                           top_user=top_user,
                           recipes=recipes,
                           top_recipe=top_recipe,
                           featured_user=featured_user,
                           featured_recipe=featured_recipe,
                           categories=categories,
                           seo={
                               'title': _l('Рецептуарий - ваш персональный сборник рецептов!'),
                               'description': _l('Рецептуарий - ваш персональный сборник рецептов!'),
                               'keywords': _l('Рецептуарий - ваш персональный сборник рецептов!')
                           },
                           times=times)


@blueprint.route('/profile')
@login_required
def profile():
    times = css_js_update_time()
    return render_template('profile.html',
                           user=current_user,
                           seo={
                               'title': _l('Мой профиль'),
                               'description': _l(''),
                               'keywords': _l('')
                           },
                           times=times)


@blueprint.route('/new-recipe', methods=['GET', 'POST'])
@login_required
def new_recipe():
    times = css_js_update_time()
    form = RecipeForm()
    form.init_data()

    if form.validate_on_submit():
        try:
            user = User.objects.get(id=current_user.id)
            if not user.recipes() or True:
                add_achievement('первый рецепт', current_user.id)
            elif len(user.recipes()) == 9:
                add_achievement('десятый рецепт', current_user.id)

            ingredients = get_recipe_ingredients(request.form.getlist('ingr[]'), request.form.getlist('qty[]'))
            category = Category.objects.get(id=form.category.data)

            recipe = Recipe(user=user, category=category, title=form.title.data,
                            description=form.description.data, ingredients=ingredients,
                            normalized_description=normalize_text(form.description.data),
                            is_searchable=form.is_searchable.data)

            if form.picture.data:
                recipe.set_picture(form.picture.data)

            recipe.save()
        except Exception as ex:
            flash('Что-то пошло не так. Попробуйте еще раз :: {}'.format(str(ex)))
            return redirect(url_for('public.new_recipe'))
        else:
            flash('Рецепт успешно добавлен!')
            return redirect(url_for('public.profile'))

    return render_template('manage_recipe.html',
                           form=form,
                           seo={
                               'title': _l('Новый рецепт'),
                               'description': _l(''),
                               'keywords': _l('')
                           },
                           times=times)


@blueprint.route('/edit-recipe/<recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    times = css_js_update_time()
    recipe = Recipe.objects.get_or_404(id=recipe_id)

    if recipe.user.id != current_user.id:
        abort(403)

    form = RecipeForm()
    form.init_data()

    if form.validate_on_submit():
        ingredients = get_recipe_ingredients(request.form.getlist('ingr[]'), request.form.getlist('qty[]'))
        category = Category.objects.get(id=form.category.data)

        recipe.title = form.title.data
        recipe.category = category
        recipe.ingredients = ingredients
        recipe.difficulty = form.difficulty.data
        recipe.cooking_time = form.cooking_time.data
        recipe.description = form.description.data
        recipe.normalized_description = normalize_text(form.description.data)
        recipe.is_searchable = form.is_searchable.data
        recipe.updated = datetime.utcnow()

        if form.picture.data or request.form.get('delete_picture'):
            recipe.delete_picture()
            if form.picture.data:
                recipe.set_picture(form.picture.data)

        recipe.save()

        return redirect(url_for('public.edit_recipe', recipe_id=recipe.id))

    return render_template('manage_recipe.html',
                           recipe=recipe,
                           form=form,
                           seo={
                               'title': recipe.title,
                               'description': _l(''),
                               'keywords': _l('')
                           },
                           times=times)


@blueprint.route('/delete-recipe/<recipe_id>')
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.objects.get_or_404(id=recipe_id)
    if recipe.user.id != current_user.id:
        abort(403)

    recipe.delete_picture()
    recipe.delete()

    return redirect(url_for('public.profile'))


@blueprint.route('/like-recipe/<recipe_id>', methods=['POST'])
def like_recipe(recipe_id):
    if not current_user.is_authenticated:
        return jsonify({'error': _l('Вы должны быть авторизованными в системе!')}), 403
    try:
        recipe = Recipe.objects.get(id=recipe_id, likes__user__ne=current_user.id)
    except DoesNotExist:
        return jsonify({'error': _l('Рецепт уже добавлен в избранное!')}), 404
    else:
        recipe.likes.append(RecipeLike(user=User.objects.get(id=current_user.id)))
        recipe.save()
        return jsonify({'ok': _l('Рецепт успешно добавлен в список избранных.')}), 200


@blueprint.route('/recipe-pic/<file_id>')
def recipe_pic(file_id):
    try:
        recipe = Recipe.objects.get_or_404(picture=ObjectId(file_id))
        picture = recipe.get_picture()
        response = make_response(picture.read())
        response.mimetype = 'image/jpeg'
        return response
    except NoFile:
        abort(404)
    except InvalidId:
        abort(404)


@blueprint.route('/recipe/<recipe_id>')
def recipe(recipe_id):
    times = css_js_update_time()
    recipe = Recipe.objects.get_or_404(id=recipe_id)

    return render_template('recipe.html',
                           seo={
                               'title': recipe.title,
                               'description': recipe.title,
                               'keywords': recipe.title
                           },
                           recipe=recipe,
                           times=times)


@blueprint.route('/recipes/')
def recipes():
    page = request.args.get('page', 1, type=int)
    times = css_js_update_time()
    categories = Category.objects().order_by('order')
    recipes = Recipe.objects(is_searchable=True).order_by('-added').paginate(page=page, per_page=current_app.config['RECIPES_PER_PAGE'])
    return render_template('recipes_list.html',
                           recipes=recipes,
                           categories=categories,
                           seo={
                               'title': _l('Рецепты пользователей рецептуария'),
                               'description': _l('Рецепты пользователей рецептуария'),
                               'keywords': _l('Рецепты пользователей рецептуария')
                           },
                           times=times)


@blueprint.route('/recipes/category/<slug>')
def recipes_by_category(slug):
    page = request.args.get('page', 1, type=int)
    times = css_js_update_time()
    categories = Category.objects().order_by('order')
    category = Category.objects.get_or_404(slug=slug)
    recipes = Recipe.objects(category=category, is_searchable=True).order_by('-added').paginate(page=page, per_page=current_app.config['RECIPES_PER_PAGE'])
    return render_template('recipes_list.html',
                           recipes=recipes,
                           current_category=category,
                           categories=categories,
                           seo={
                               'title': category.name,
                               'description': category.name,
                               'keywords': category.name
                           },
                           times=times)


@blueprint.route('/recipes/by-author/<author_id>')
def recipes_by_author(author_id):
    page = request.args.get('page', 1, type=int)
    times = css_js_update_time()
    user = User.objects.get_or_404(id=author_id)
    recipes = Recipe.objects(user=user, is_searchable=True).order_by('-added').paginate(page=page, per_page=current_app.config['RECIPES_PER_PAGE'])
    if not recipes:
        abort(404)

    return render_template('recipes_list.html',
                           recipes=recipes,
                           user=user,
                           seo={
                               'title': '{} {}'.format(_l('Рецепты от'), user.username),
                               'description': '{} {}'.format(_l('Рецепты от'), user.username),
                               'keywords': '{} {}'.format(_l('Рецепты от'), user.username)
                           },
                           times=times)


@blueprint.route('/contacts', methods=['GET', 'POST'])
def contacts():
    times = css_js_update_time()
    form = ContactForm()

    if form.validate_on_submit():
        user = None if not current_user.is_authenticated else User.objects.get(id=current_user.id)
        feedback = Feedback(user=user,
                            name=form.name.data, email=form.email.data, message=form.message.data)
        feedback.save()

        msg = "<p>Добрый день!</p>" \
              "<p>Кто-то оставил сообщение на сайте Рецептуария.</p>" \
              "<p>Пользователь: <a href='https://xn--80ajanf7aeeqk3a.xn--p1ai{}'>{}</a></p>" \
              "<p>Представился: {}</p>" \
              "<p>Email: {}</p>" \
              "<p>Сообщение: {}</p>" \
              "<br><br><p>С уважением,<br>команда Рецептуария.</p>"\
            .format(
                url_for('public.recipes_by_author', author_id=feedback.user.id) if feedback.user else '#',
                feedback.user.username if feedback.user else '-',
                feedback.name, feedback.email, feedback.message
            )
        send_email(_('Сообщение с сайта'), current_app.config['SENDER'], current_app.config['ADMINS'],
                   msg, msg)

        flash(_l('Сообщение было успешно отослано, спасибо!'))
        return redirect(url_for('public.contacts'))

    return render_template('contacts.html',
                           form=form,
                           times=times)


@blueprint.route('/bot')
def bot():
    times = css_js_update_time()
    return render_template('bot.html',
                           times=times)


@blueprint.route('/search')
def search():
    times = css_js_update_time()
    form = SearchForm()
    form.init_data()

    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')

    recipes = Recipe.search(keyword, request.args.get('category', ''), page)

    return render_template('search.html',
                           form=form,
                           category=category,
                           recipes=recipes,
                           keyword=keyword,
                           seo={
                               'title': _l('Результаты поиска'),
                               'description': '',
                               'keywords': ''
                           },
                           times=times)

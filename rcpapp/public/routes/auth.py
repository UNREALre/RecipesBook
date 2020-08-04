# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, session, url_for, current_app, flash
from flask_mongoengine import DoesNotExist
from flask_babel import lazy_gettext as _l, _
from flask_login import current_user, login_user, logout_user
import secrets
from rcpapp.public import blueprint
from rcpapp.models import User, PassRecovery
from rcpapp.public.forms import LoginForm, RegistrationForm, PasswordRecoveryForm, PasswordResetForm
from rcpapp.helper import css_js_update_time
from rcpapp.public.email import send_email


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.objects.get(username=form.username.data)
            if not user.check_password(form.password.data):
                flash(_l('Неверный пароль'))
                return redirect(url_for('public.login'))
        except DoesNotExist:
            flash(_l('Пользователя не существует в системе'))
            return redirect(url_for('public.login'))
        else:
            login_user(user, form.remember_me.data)
            # check if user comes from any protected non-anonymous page to return him where he wanted to be before login
            next_page = request.args.get('next') or url_for('public.index')
            return redirect(next_page)

    times = css_js_update_time()
    return render_template('login.html', form=form, times=times)


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    times = css_js_update_time()
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.save()

        flash(_l('Поздравляем, Вы успешно зарегистрировались!'))
        return redirect(url_for('public.login'))

    return render_template('register.html', form=form, times=times)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))


@blueprint.route('/recover', methods=['GET', 'POST'])
def password_recovery():
    times = css_js_update_time()
    form = PasswordRecoveryForm()
    if form.validate_on_submit():
        user = User.objects.get(email=form.email.data)
        recover = PassRecovery(user=user, recovery_hash=secrets.token_urlsafe(16)).save()

        reset_url = 'https://рецептуарий.рф{}'.format(url_for('public.recover_reset',
                                                              uid=user.id, hash=recover.recovery_hash))
        recovery_msg = "<p>Добрый день!</p>" \
                       "<p>Мы получили запрос на восстановление пароля. Для сброса пароля и установки нового, " \
                       "пожалуйста, перейдите по <a href='{}' target='_blank'>ссылке</a>.</p>" \
                       "<br><br><p>С уважением,<br>команда Рецептуария.</p>".format(reset_url)
        send_email(_('Восстановление пароля'), current_app.config['SENDER'], [user.email],
                   recovery_msg, recovery_msg)

        flash(_l('Ссылка на восстановление пароля успешно отправлена на указанный E-mail.'))
        return redirect(url_for('public.login'))

    return render_template('password_recovery.html', form=form, times=times)


@blueprint.route('/recover/reset/<uid>/<hash>', methods=['GET', 'POST'])
def recover_reset(uid, hash):
    try:
        user = User.objects.get(id=uid)
    except DoesNotExist:
        flash('Неверная ссылка для восстановления пароля! Пользователя не найдено в системе.')
        return redirect(url_for('public.login'))
    else:
        try:
            recover = PassRecovery.objects.get(recovery_hash=hash)
        except DoesNotExist:
            flash('Неверная ссылка для восстановления пароля! Неверный секретный код.')
            return redirect(url_for('public.login'))
        else:
            times = css_js_update_time()
            form = PasswordResetForm()
            if form.validate_on_submit():
                user.set_password(form.password.data)
                user.save()
                recover.delete()
                flash('Пароль успешно изменён!')
                return redirect(url_for('public.login'))

            return render_template('password_reset.html', form=form, times=times)

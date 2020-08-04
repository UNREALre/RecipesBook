# -*- coding: utf-8 -*-
from flask import session, request
from datetime import datetime
from flask_babel import lazy_gettext as _l
import re
from jinja2 import evalcontextfilter, Markup


def add_context(app):
    @app.context_processor
    def inject_lang():
        lang = session.get('lang') if not request.args.get('lang') else request.args.get('lang')
        return {'lang': lang}

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.context_processor
    def utility_processor():
        def get_recipe_difficulty(difficulty, for_css=False):
            if difficulty == 1:
                result = _l("легко") if not for_css else "easy"
            elif difficulty == 2:
                result = _l("средне") if not for_css else "medium"
            else:
                result = _l("сложно") if not for_css else "hard"

            return result

        def get_category_class(loop_index):
            if loop_index % 3 == 0:
                css_class = 'dark'
            elif loop_index % 2 == 0:
                css_class = 'medium'
            else:
                css_class = 'light'

            return css_class

        return dict(get_recipe_difficulty=get_recipe_difficulty,
                    get_category_class=get_category_class)

    @app.template_filter()
    @evalcontextfilter
    def nl2br(eval_ctx, value):
        """Converts newlines in text to HTML-tags"""

        value = re.sub(r'\r\n|\r|\n', '\n', value)  # normalize newlines
        paras = re.split('\n{2,}', value)
        paras = [u'<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
        paras = u'\n\n'.join(paras)
        return Markup(paras)

# -*- coding: utf-8 -*-
from rcpapp import create_app, cli, context

rcpapp = create_app()
cli.register(rcpapp)
context.add_context(rcpapp)

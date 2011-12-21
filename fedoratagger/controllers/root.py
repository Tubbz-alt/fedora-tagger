# -*- coding: utf-8 -*-
"""Main Controller"""

import random

from tg import expose, flash, require, url, lurl, request, redirect
from tg.i18n import ugettext as _, lazy_ugettext as l_
from paste.deploy.converters import asbool
from fedoratagger import model
from repoze.what import predicates
from fedoratagger.controllers.secure import SecureController
from fedoratagger.model import DBSession, metadata

from fedoratagger.lib.base import BaseController
from fedoratagger.controllers.error import ErrorController
from fedoratagger.controllers.radial import RadialController

from fedoratagger.widgets.card import CardWidget

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the fedora-tagger application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()

    error = ErrorController()

    radial = RadialController()

    @expose('fedoratagger.templates.index')
    def index(self):
        """Handle the front-page."""
        redirect(url('/tagger'))

    @expose('fedoratagger.templates.tagger')
    def tagger(self):
        packages = model.Package.query.all()
        n = len(packages)
        cards = [
            CardWidget(package=packages[random.randint(0, n-1)])
            for i in range(3)
        ]
        cards[1].css_class = 'card center'
        return dict(cards=cards)

    @expose('json')
    def vote(self, id, like):
        tag = model.Tag.query.filter_by(id=id).one()

        if asbool(like):
            tag.like += 1
        else:
            tag.dislike += 1

        return tag.__json__()

    @expose('fedoratagger.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('fedoratagger.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('fedoratagger.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a data page and a display page"""
        return dict(params=kw)
    @expose('fedoratagger.templates.authentication')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth')

    @expose('fedoratagger.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('fedoratagger.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('fedoratagger.templates.login')
    def login(self, came_from=lurl('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login',
                params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)
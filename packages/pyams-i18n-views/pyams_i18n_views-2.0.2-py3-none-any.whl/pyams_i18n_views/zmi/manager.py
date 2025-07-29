#
# Copyright (c) 2015-2021 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_i18n_views.zmi.manager module

This module provides components used to handle languages selection.
"""

from pyams_form.ajax import ajax_form_config
from pyams_form.field import Fields
from pyams_i18n.interfaces import II18nManager
from pyams_layer.interfaces import IPyAMSLayer
from pyams_security.interfaces import IViewContextPermissionChecker
from pyams_security.interfaces.base import MANAGE_PERMISSION, VIEW_SYSTEM_PERMISSION
from pyams_skin.interfaces.viewlet import IHelpViewletManager
from pyams_skin.viewlet.help import AlertMessage
from pyams_utils.adapter import ContextRequestViewAdapter, adapter_config
from pyams_viewlet.viewlet import viewlet_config
from pyams_zmi.form import AdminEditForm
from pyams_zmi.interfaces import IAdminLayer
from pyams_zmi.interfaces.viewlet import ISiteManagementMenu
from pyams_zmi.zmi.viewlet.menu import NavigationMenuItem


__docformat__ = 'restructuredtext'

from pyams_i18n_views import _


@viewlet_config(name='languages.menu',
                context=II18nManager, layer=IAdminLayer,
                manager=ISiteManagementMenu, weight=100,
                permission=VIEW_SYSTEM_PERMISSION)
class I18nManagerLanguagesMenu(NavigationMenuItem):
    """I18n manager languages menu"""

    label = _("Languages")
    icon_class = 'fas fa-flag'

    href = '#languages.html'


@ajax_form_config(name='languages.html',
                  context=II18nManager, layer=IPyAMSLayer,
                  permission=VIEW_SYSTEM_PERMISSION)
class I18nManagerLanguagesEditForm(AdminEditForm):
    """I18n manager languages edit form"""

    title = _("Content translations")
    legend = _("Content languages")

    fields = Fields(II18nManager)
    _edit_permission = None


@viewlet_config(name='languages.help',
                context=II18nManager, layer=IAdminLayer, view=I18nManagerLanguagesEditForm,
                manager=IHelpViewletManager, weight=10)
class I18nManagerLanguagesEditFormHelp(AlertMessage):
    """I18n manager languages edit form help"""

    _message = _("For each selected language, a tab will be associated to each *translatable* "
                 "form input to enter matching translation.")

    message_renderer = 'markdown'


@adapter_config(required=(II18nManager, IPyAMSLayer, I18nManagerLanguagesEditForm),
                provides=IViewContextPermissionChecker)
class I18nManagerLanguageEditFormPermissionChecker(ContextRequestViewAdapter):
    """I18n manager language edit form permission checker"""

    edit_permission = MANAGE_PERMISSION

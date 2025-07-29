#
# Copyright (c) 2015-2020 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_i18n_views.zmi.negotiator module

This module defines views and content providers for I18n negotiator utility management
interface.
"""

from zope.interface import Interface

from pyams_form.ajax import ajax_form_config
from pyams_form.browser.checkbox import SingleCheckBoxFieldWidget
from pyams_form.field import Fields
from pyams_i18n.interfaces import INegotiator
from pyams_layer.interfaces import IPyAMSLayer
from pyams_security.interfaces.base import MANAGE_SYSTEM_PERMISSION
from pyams_utils.adapter import adapter_config
from pyams_zmi.form import AdminModalEditForm
from pyams_zmi.interfaces import IAdminLayer, IObjectLabel
from pyams_zmi.interfaces.table import ITableElementEditor
from pyams_zmi.table import TableElementEditor


__docformat__ = 'restructuredtext'

from pyams_i18n_views import _  # pylint: disable=ungrouped-imports


@adapter_config(required=(INegotiator, IAdminLayer, Interface),
                provides=IObjectLabel)
def negotiator_label(context, request, view):
    """I18n negotiator label"""
    return request.localizer.translate(_("Language negotiator"))


@adapter_config(required=(INegotiator, IAdminLayer, Interface),
                provides=ITableElementEditor)
class NegotiatorEditor(TableElementEditor):
    """I18n negotiator editor adapter"""


@ajax_form_config(name='properties.html', context=INegotiator, layer=IPyAMSLayer)
class NegotiatorPropertiesEditForm(AdminModalEditForm):
    """I18n negotiator properties edit form"""

    title = _("Language negotiator")
    legend = _("Properties")

    fields = Fields(INegotiator)
    fields['cache_enabled'].widget_factory = SingleCheckBoxFieldWidget

    _edit_permission = MANAGE_SYSTEM_PERMISSION

#
# Copyright (c) 2015-2019 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS I18n views.interfaces module

"""

from zope.interface import Attribute

from pyams_form.interfaces.widget import IWidget


class II18nWidget(IWidget):
    """I18n widget marker interface"""

    languages = Attribute("Widget languages")

    widget_factory = Attribute("Custom inner widget factory")

    widgets = Attribute("Widgets list")

    def get_widget(self, lang):
        """Get widget matching given language"""

    def get_value(self, lang):
        """Get value matching given language"""

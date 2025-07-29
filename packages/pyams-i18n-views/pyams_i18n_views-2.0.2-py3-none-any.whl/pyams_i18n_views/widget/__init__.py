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

"""PyAMS_i18n_views.widget module

This module defines custom widgets which are used to handle input and display of
I18n forms fields.
"""

from collections import OrderedDict

from pyramid.decorator import reify
from zope.component import getMultiAdapter, queryMultiAdapter
from zope.interface import alsoProvides, implementer_only
from zope.schema import ValidationError
from zope.schema.fieldproperty import FieldProperty

from pyams_form.browser.widget import HTMLInputWidget
from pyams_form.converter import BaseDataConverter
from pyams_form.interfaces import DISPLAY_MODE, HIDDEN_MODE, IDataConverter, INPUT_MODE, \
    IValidator
from pyams_form.interfaces.error import IErrorViewSnippet
from pyams_form.interfaces.form import IFormAware
from pyams_form.interfaces.widget import IFieldWidget, IWidget
from pyams_form.template import widget_template_config
from pyams_form.util import expand_prefix
from pyams_form.widget import FieldWidget, Widget
from pyams_i18n.interfaces import II18nManager, INegotiator
from pyams_i18n.schema import II18nField
from pyams_i18n_views.interfaces import II18nWidget
from pyams_layer.interfaces import IPyAMSLayer
from pyams_utils.adapter import adapter_config
from pyams_utils.interfaces.form import NO_VALUE
from pyams_utils.registry import query_utility
from pyams_utils.traversing import get_parent


__docformat__ = 'restructuredtext'


@adapter_config(required=(II18nField, II18nWidget),
                provides=IDataConverter)
class I18nDataConverter(BaseDataConverter):
    """I18n base data converter"""

    def to_widget_value(self, value):
        result = {}
        if value is None:
            return result
        for lang, val in value.items():
            converter = queryMultiAdapter((self.field.value_type, self.widget.get_widget(lang)),
                                          IDataConverter)
            if converter is not None:
                result[lang] = converter.to_widget_value(val)
        return result

    def to_field_value(self, value):
        result = {}
        for lang in self.widget.languages:
            converter = queryMultiAdapter((self.field.value_type, self.widget.get_widget(lang)),
                                          IDataConverter)
            if converter is not None:
                result[lang] = converter.to_field_value(self.widget.get_value(lang))
        return result


@widget_template_config(mode=INPUT_MODE,
                        template='templates/i18n-input.pt', layer=IPyAMSLayer)
@widget_template_config(mode=DISPLAY_MODE,
                        template='templates/i18n-input.pt', layer=IPyAMSLayer)
@widget_template_config(mode=HIDDEN_MODE,
                        template='templates/i18n-hidden.pt', layer=IPyAMSLayer)
@implementer_only(II18nWidget)
class I18nWidget(HTMLInputWidget, Widget):
    """I18n base widget"""

    _mode = FieldProperty(IWidget['mode'])

    widgets = None
    widget_factory = None

    @reify
    def languages(self):
        """Widget languages getter"""
        result = []
        negotiator = query_utility(INegotiator)
        if negotiator is not None:
            result.append(negotiator.server_language)
        manager = get_parent(self.context, II18nManager)
        if manager is not None:
            result.extend(sorted(filter(lambda x: x not in result,
                                        manager.languages or ())))
        elif negotiator is not None:
            result.extend(sorted(filter(lambda x: x not in result,
                                        negotiator.offered_languages or ())))
        else:
            result.append('en')
        return result

    def update(self):
        widgets = self.widgets = OrderedDict()
        for lang in self.languages:
            if self.widget_factory is not None:
                # pylint: disable=not-callable
                widget = self.widget_factory(self.field.value_type, self.request)
            else:
                widget = queryMultiAdapter((self.field.value_type, self.request),
                                           IFieldWidget)
            if widget is not None:
                base_prefix = expand_prefix(self.form.prefix) + \
                              expand_prefix(self.form.widgets.prefix)
                prefix = base_prefix + expand_prefix(lang)
                name = self.field.value_type.__name__ = self.field.__name__
                widget.mode = self.mode
                widget.basename = base_prefix + name
                widget.name = prefix + name
                widget.id = widget.name.replace('.', '-')
                if IFormAware.providedBy(self):
                    widget.form = self.form
                    alsoProvides(widget, IFormAware)
                widget.field = self.field.value_type
                widget.context = self.context
                widget.ignore_context = self.ignore_context
                widget.ignore_request = self.ignore_request
                widget.language = lang
                widget.update()
            widgets[lang] = widget
        super().update()
        for lang in self.languages:
            widget = self.widgets[lang]
            value = (self.value or {}).get(lang, NO_VALUE)
            if value is not NO_VALUE:
                try:
                    # pylint: disable=assignment-from-no-return
                    converter = IDataConverter(widget)
                    field_value = converter.to_field_value(value)
                    getMultiAdapter((self.context, self.request, self.form, widget.field,
                                     self.form), IValidator).validate(field_value)
                    widget.value = converter.to_widget_value(field_value)
                except (ValidationError, ValueError) as error:
                    view = getMultiAdapter((error, self.request, widget, widget.field, self.form,
                                            self.context), IErrorViewSnippet)
                    view.update()
                    widget.error = view
                    widget.value = value

    @property
    def mode(self):
        """Mode getter"""
        return self._mode

    @mode.setter
    def mode(self, value):
        """Mode setter"""
        if self.widgets:
            for lang in self.languages:
                self.widgets[lang].mode = value
        self._mode = value

    def extract(self, default=NO_VALUE):
        result = {}
        # pylint: disable=expression-not-assigned
        [result.setdefault(lang, self.widgets[lang].extract(default))
         for lang in self.languages]
        for value in result.values():
            if value is not NO_VALUE:
                return result
        return default

    def get_widget(self, lang):
        """Widget getter for specified language"""
        return self.widgets.get(lang)

    def get_value(self, lang):
        """Value getter for specified language"""
        return self.get_widget(lang).value

    def set_widgets_attr(self, key, value):
        """Widgets attribute setter"""
        for widget in self.widgets.values():
            setattr(widget, key, value)

    def add_widgets_class(self, klass):
        """Widgets CSS class setter"""
        for widget in self.widgets.values():
            widget.add_class(klass)


@adapter_config(required=(II18nField, IPyAMSLayer), provides=IFieldWidget)
def I18nFieldWidget(field, request):  # pylint: disable=invalid-name
    """I18n field widget factory"""
    return FieldWidget(field, I18nWidget(request))

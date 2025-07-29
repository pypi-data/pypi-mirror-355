========================
PyAMS I18n views package
========================

Introduction
------------

This package is composed of a set of utility functions, usable into any Pyramid application.

    >>> import pprint

    >>> from pyramid.testing import setUp, tearDown, DummyRequest
    >>> config = setUp(hook_zca=True)
    >>> config.registry.settings['zodbconn.uri'] = 'memory://'

    >>> from pyramid_zodbconn import includeme as include_zodbconn
    >>> include_zodbconn(config)
    >>> from cornice import includeme as include_cornice
    >>> include_cornice(config)
    >>> from pyams_utils import includeme as include_utils
    >>> include_utils(config)
    >>> from pyams_site import includeme as include_site
    >>> include_site(config)
    >>> from pyams_i18n import includeme as include_i18n
    >>> include_i18n(config)
    >>> from pyams_form import includeme as include_form
    >>> include_form(config)
    >>> from pyams_skin import includeme as include_skin
    >>> include_skin(config)
    >>> from pyams_zmi import includeme as include_zmi
    >>> include_zmi(config)
    >>> from pyams_i18n_views import includeme as include_i18n_views
    >>> include_i18n_views(config)

    >>> request = DummyRequest(headers={'Accept-Language': 'en'})
    >>> from pyams_site.generations import upgrade_site
    >>> app = upgrade_site(request)
    Upgrading PyAMS timezone to generation 1...
    Upgrading PyAMS I18n to generation 1...


I18n widgets
------------

PyAMS provides custom widgets to handle I18n form fields:

    >>> from pyams_utils.adapter import adapter_config
    >>> from pyams_utils.testing import call_decorator

    >>> from zope.interface import alsoProvides, implementer, Interface
    >>> from pyams_i18n.schema import I18nTextLineField

    >>> class II18nContent(Interface):
    ...     title = I18nTextLineField(title="Title")

    >>> from zope.schema.fieldproperty import FieldProperty

    >>> @implementer(II18nContent)
    ... class I18nContent:
    ...     title = FieldProperty(II18nContent['title'])

    >>> from pyams_form.field import Fields
    >>> from pyams_form.form import EditForm

    >>> class I18nContentEditForm(EditForm):
    ...     fields = Fields(II18nContent)

    >>> from pyams_layer.interfaces import IFormLayer

We can now create our content and initialize a form:

    >>> from pyams_layer.interfaces import IPyAMSLayer

    >>> content = I18nContent()
    >>> content.title = {'en': "Content title"}

    >>> request = DummyRequest()
    >>> alsoProvides(request, IPyAMSLayer)

    >>> form = I18nContentEditForm(content, request)
    >>> form.update()
    >>> form.widgets
    FieldWidgets([('title', <I18nWidget 'form.widgets.title'>)])

    >>> print(form.widgets['title'].render().strip())
    <div id="form-widgets-title">
        <input type="text"
               id="form-widgets-en-title"
               name="form.widgets.en.title"
               class="form-control text-widget textline-field"
               value="Content title" />
    </div>

Let's now try to add an I18n negotiator to add a few languages:

    >>> from pyams_utils.registry import set_local_registry
    >>> set_local_registry(app.getSiteManager())

    >>> negotiator = app.getSiteManager()['Language negotiator']
    >>> negotiator.offered_languages = {'en', 'fr'}

    >>> form = I18nContentEditForm(content, request)
    >>> form.update()
    >>> widget = form.widgets['title']

    >>> widget.languages
    ['en', 'fr']
    >>> widget.mode
    'input'
    >>> widget.get_widget('en')
    <TextWidget 'form.widgets.en.title'>
    >>> widget.get_value('en')
    'Content title'

    >>> widget.set_widgets_attr('rows', 5)
    >>> widget.get_widget('en').rows
    5

    >>> widget.add_widgets_class('custom-klass')
    >>> widget.get_widget('en').klass
    'text-widget textline-field custom-klass'

    >>> widget.mode = 'display'
    >>> widget.get_widget('en').mode
    'display'

    >>> request = DummyRequest(params={'form.widgets.en.title': "New content",
    ...                                'form.buttons.apply': "Apply"})
    >>> alsoProvides(request, IPyAMSLayer)

    >>> form = I18nContentEditForm(content, request)
    >>> form.update()
    >>> pprint.pprint(content.title)
    {'en': 'New content', 'fr': None}


Tests cleanup:

    >>> tearDown()

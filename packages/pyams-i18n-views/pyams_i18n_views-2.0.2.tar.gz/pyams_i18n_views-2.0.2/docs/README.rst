========================
PyAMS I18n views package
========================

.. contents::


What is PyAMS?
==============

PyAMS (Pyramid Application Management Suite) is a small suite of packages written for applications
and content management with the Pyramid framework.

**PyAMS** is actually mainly used to manage web sites through content management applications (CMS,
see PyAMS_content package), but many features are generic and can be used inside any kind of web
application.

All PyAMS documentation is available on `ReadTheDocs <https://pyams.readthedocs.io>`_; source code
is available on `Gitlab <https://gitlab.com/pyams>`_ and pushed to `Github
<https://github.com/py-ams>`_. Doctests are available in the *doctests* source folder.


What is PyAMS I18n views?
=========================

PyAMS I18n package provides features to handle content internationalization, to be able to
provide contents into several languages (not speaking here of "dead" text, handled by Gettext,
but of "user" text, entered for example in a CMS).

This package is adding views and content providers and a management interface to configure
server's I18n negotiator utility, and is also adding dedicated widgets which can be used to
enter contents into several languages.

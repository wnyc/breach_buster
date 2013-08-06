BREACH_BUSTER
=============

Django middleware that (hopefully) protects against the SSL BREACH vulnerability.

To use replace django.middlware.Gzip with
breach_buster.middleware.Gzip in your settings file MIDDLEWARE_CLASSES
variable.


To install run pip install djang_breach_buster

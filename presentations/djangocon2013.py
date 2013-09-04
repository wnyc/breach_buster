#!/usr/bin/env python
# -*- coding: utf-8 -*-

from prysenter import Prysentation, pechakucha

try:
    from prysenter.formatters import bulletpoints as bp
    from prysenter.formatters import outline as ol
    from prysenter.formatters import items as items
except:
    print "Use the version of prysenter from wnyc/prysenter"
    raise 

from prysenter.formatters import multiline as mu
from prysenter.formatters import subtitle as st
from prysenter.formatters import code_subtitle as ct

slides = [
    st('Breach Buster',
       'BREACH resistant GzipMiddleware',
       'http://github.com/wnyc/breach_buster',
       'Adam DePrince - adeprince@nypublicradio.org',
       'DjangoCon US Lighting Talks - September 4th 2013'),
    bp('BREACH attack requires ... ',
       'A request on victim\'s behalf',
       'Secret with known prefix',
       'Request parameter echoed in response',
       'Attacker can measure SSL response size'),
    ol('Mitigations recommended by Prado, Harris and Gluck',
       'Disable HTTP compression',
       'Seperate secrets from user input',
       'Randomize secrets per request',
       'Mask secrets',
       'CSRF',
       'Length hiding <- Breach_buster\'s apprach',
       'Rate limiting'),
    items('BREACH_BUSTER implements length hiding',
          '',
          'Calls flush randomly',
          'PRNG seeded from content hash',
          '(averaging attack resistant)'),
    items('Quick demo',
          'Search for:',
          '<a href="do_something?CSRF=f675d2395f243c89">',
          '',
          'Accept parameter: name=',
          '<h2>Hello %(name)s</h2>'
          ),
    st('Breach Buster',
       'BREACH resistant GzipMiddleware',
       'http://github.com/wnyc/breach_buster',
       '',
       'Ticket: https://code.djangoproject.com/ticket/20869',
       '',
       'Pull req: https://github.com/django/django/pull/1473',
       '',
       'Adam DePrince - adeprince@nypublicradio.org',
       'DjangoCon US Lighting Talks - September 4th 2013'),
    ]


Prysentation(slides=slides).start()


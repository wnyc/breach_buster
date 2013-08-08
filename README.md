BREACH_BUSTER
=============

Django gzip middleware replacement that protects against SSL BREACH
vulnerability by randomizing the length of the compressed stream.

Usage
-----

Install breach buster

    $ pip install breach_buster

Open your settings.py file in an editor and modifiy it to

    MIDDLEWARE_CLASSES = (
        'django.middleware.gzip.GZipMiddleware',
        'johnny.middleware.LocalStoreClearMiddleware',

replace django's GzipMiddleware with breach buster's.  

    MIDDLEWARE_CLASSES = (
        'breach_buster.middleware.gzip.GZipMiddleware',
        'johnny.middleware.LocalStoreClearMiddleware',


Detailed Explanation
--------------------

BREACH is a side channel attack that takes advantage of a well known
characteristic of data compression: files that are self similar will
tend to be smaller.   This is used to 

Lets take a look at what that means.  In the code below we feed two
sentences to the zlib compressor.  Both sentences are the same length,
except the latter replaces dog with fox, a string that was already
used.

    >>> import zlib
    >>> len(zlib.compress('The quick brown fox jumps over the lazy dog'))
    50
    >>> len(zlib.compress('The quick brown fox jumps over the lazy fox'))
    47
    >>> 


The later compresses to 3 bytes less than the former.  You might be
thinking "well that's a bad example, the so called compression made
the file larger". True, but the same applies to larger files as well.
Lets try again with a longer example.

Here we download a copy of the Wikipedia article on the the Communist
Manifesto.  To prepare two files that are different we append to one
the word "Proletariat" and to the other the slightless less like to
appear "Adirondacks".

    >>> import zlib, urllib2 
    >>> prose = urllib2.urlopen("http://www.marxists.org/archive/marx/works/1848/communist-manifesto/ch01.htm").read()

    >>> proletariat = prose + "Proletariat"
    >>> adirondacks = prose + "Adirondacks"
    >>> len(proletariat)
    35968
    >>> len(adirondacks)
    35968
    >>> len(zlib.compress(proletariat))
    13107
    >>> len(zlib.compress(adirondacks))
    13113
    >>> 


We can see the file with Proletariat added is somewhat smaller than
the file with Adriondacks added.

So how does BREACH take advantage of this?

It is assumed an attacker using BREACH has three non-trivial to obtain abilities.  

First, we assume the attacker has the ability to monitor the victim's
internet connection.  This can happen in many ways.  The attacker can
be sniffing the victim's local wifi or ethernet connection, they can
work for the victim's ISP.  All they need to do is be able to see the
data common back well enough to measure the length of each response. 

Secondly we assume the attacker has some way of coersing the victims
browser to load urls at will.  We assume this doesn't mean the attacker can
see the content that comes back - if the attacker could this entire
exercise would be moot - they only need to log in as themselves.   

Third, the page must be willing to return information passed to it by
the client.  This entire attack depends on the ability to inject data
into the HTTP content.  Normally this isn't too hard - perhaps there
is a form field the web server will happily fill for you?  Name or
something?

It i important to stress that the attacker should know what they are
looking for.  This attack cannot give us the contents of the page, it
can only betray a small peice.  If the attacker has already visited
this site and knows the secret to be in a field called
`"uber_secret_api_key=<8 digit hexidecimal number>"` then this attack
will work.  If we've never seen this page because we cannot coerse the
browser to make a copy for us sans the secrets we are looking for,
this attack won't work.

There are all sorts of ways we could achive these three requirements.
You could intercept non-encrytped web traffic and inject a little HTML
that looks something like this: `<img
href="http://victimsbank.com/...">` You could setup a transparent web
proxy in their emplyoer's data cabinet.  Or you could simply email
them a link to a website with pictures of pretty undressed people.

Nothing I describe here is too hard to come by for a moderately
sophisticated geek.  And with this in mind we're going to build a
BREACH attack.


Let's Breach
------------

Before we do, lets talk about what we won't be doing.  This isn't a
lesson on coering browsers to send urls or sniffing Wifi so we're
going to cheat.  This example won't use SSL or a browser.  Its a
demonstration, an educational tool, not a fully weaponized attack
platform for script kiddies.

Now there are a few more requrements to conducting a successful breach
attack that need to be mentioned.  First it helps to understand what
you are looking for --- breach won't give you.

Lets install breach_buster.

`$ pip install breach_buster`

Now in one window lets open the breach buster web server.  It has two
pages, /good and /bad.  Each contains a CSRF key called "CSRF" that
refers to a 16 digit sequence of lower case letters or underscores.
Both urls use gzip content encoding; the /bad emulates django's gzip
content conciding strategy.  /good uses breach_buster's content
encoding.

Lets run the breach_buster_demo_server and put it in the background:

`$ breach_buster_demo_server 127.0.0.1:8080 &`

This server is also very friendly; the returned content will call you
by name if provided a parameter called "name."  This is how we inject content into the site.

Open a window to your python interepter and lets start writing a bit of code. 

    >>> import urllib2 
    >>> def length(name):
    ...     return len(urllib2.urlopen('http://127.0.0.1:8080/bad?name=' + name).read())
    ...

The breach_buster_demo_server and urllib2 both have conveniennt bugs
for this project.  breach_buster_demo_server doesn't check if the
client supports gzip encoding before using it.  urllib2 doesn't
support gzip encoding.  The call to .read returns the compressed data
content directly off the wire.

    >>> length('')
    883

Lets try adding a few strings.

    >>> length('foobar')
    887

    >>> length('elephant')
    886

    >>> length('do_something?CSRF=')
    886

We expect `do_something?CSRF=` to add relatively little data
proportional to the length of the added string because this string
already exists in the output.

Lets try all possiable combinations of first letters:

    >>> for letter in '0123456789abcdef': print letter, length('do_something?CSRF=' + letter)
    ...
    0 888
    1 888
    2 887
    3 888
    4 888
    5 888
    6 888
    7 888
    8 888
    9 888
    a 887
    b 887
    c 887
    d 887
    e 886
    f 886

We can see that e and f are excellent consideration.  Lets try adding another letter to both e and f.

    >>> for l1 in 'ef':
    ...     for l2 in '01234566789abcdef': print l1+l2, length('do_something?CSRF=' + l1 + l2)                                                                        
    ...

    e0 888
    ...
    e9 888
    ea 887
    eb 888
    ec 888
    ed 887
    ee 887
    ef 888
    f0 888
    f1 888
    f2 887
    f3 888
    f4 888
    f5 888
    f6 886
    f7 888
    f8 888
    f9 888
    fa 887
    fb 887
    fc 887
    fd 887
    fe 886
    ff 887

f6 and fe are both excellent ... we could keep on going manually, its
much easier to automate this search.  A script to do this for you has
been provided in scripts/breach_buster_demo_client

Give it a try:

    $ python scripts/breach_busters_demo_client 
    (lots and lots of output)

    888 f675d2395f243c89 !
    Found on try# 12 5200

Try this attack against the breach_buster Gzip middle ware module.

    $ python scripts/breach_busters_demo_client --busted 
    (lots and lots of output, never ends)

It is obvious from the output the search is failing to converge and
will never find the key.  Lets look at the length of the returned
output to better understand why:

    >>> def length(name):
    ...     return len(urllib2.urlopen('http://127.0.0.1:8081/good?name=' + name).read())
    ...
    >>>
    >>> length('')
    946
    >>> length('')
    931
    >>> length('')
    985
    >>> length('')
    1028
    >>> length('')
    923
    >>> length('')
    994
    >>> length('')
    1016
    >>> length('')
    950
    >>> length('')
    979
    >>> length('')
    1045
    >>> length('')
    1011
    
    
What's happening to cause this?  First consider how gzip might be used
in an interactive session.

Zlib compression, the underlying library behind gzip, is used for more
than file compression.  Assuming the data stream you work with is
compressiable there will be far fewer characters coming oeut of the
compresssor than going in.  Gzip reads some data, processes this data,
and when it has accumulated enough, outputs the same.  Sometimes bytes
will be read without any bytes being out - by definition, if the file
is being compressed this has to happen because you have too few output
bytes to have one correspond for each and every input byte.

This can become a problem for command line interaction.  Let us
consider as a our strawman case Unix's passwd command.  The inteaction
looks something like this:

    Old password: secret
    New password: soupersekret
    New password (again): soupersekret

Within a zlib compressor this entire chunk of text might compress to a
single offset to a previously occuring sample.  The ideal behaivor for
the compressor is to hold onto text until it has the best match it can
find.

But from a useability perspective this is horrid ... if old password
is being sequestered inside the compressor to see if it might match
something better later on, you, as a user would never know what the
ssystem expects of you.

The zlib library has a function called "flush."  Flush instructs the
compressor to spit out whatever is nessesary to ensure the receiver is
able to receive and decode all of the date that has been sent to the
compressor so far.  This function instructs the zlib library to do so
even if the resulting output is compressed less efficently than it
otherwise would have been.  This usually increases the size of the
resulting data stream by a small amount.  

The Breach Buster gzip middle ware takes advantage of flush to modify
the length of the produced gzip stream without modifying the contents
of the data it encodes.  By calling flush at random points within the
file the size of the generated compressed file is increases slightly
by a random amount.  This increase in size mitigates the BREACH
vulnerability.

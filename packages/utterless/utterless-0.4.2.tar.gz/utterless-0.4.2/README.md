
Utterless
=========

> Extend Python's "unittest" to better handle "logging" messages

There's a problem when you try to run a
[unittest](https://docs.python.org/3/library/unittest.html)
test suite in a codebase which also uses the
[logging](https://docs.python.org/3/library/logging.html)
framework:
You see your nice output of dots (`...F....SS....F..`)
clogged up with lots of log messages.

For occasional cases you can supress log messages in a block
of code with `self.assertLogs(...)`.
But that doesn't scale when almost every test in your suite
generates messages.

Alternatively you can fiddle your log levels so that all log
messages get supressed.
But when you have a failing test the log messages can be
very helpful in debugging it.

Wouldn't it be great to have an alternative log runner that
captures all log messages.
If the test fails the messages get displayed with the error traceback.
But if the test succeeds then the log messages get silently discarded.

Look no further!
This is possibly the package you want.

Usage
-----

We assume you already have a test suite that you run something like this:

    $ python -m unittest discover

Having installed `utterless` you just need to replace that with:

    $ python -m utterless discover

Optional Usage
--------------

Utterless has mechanisms to integrate with some frameworks that
don't run tests through `unittest` directly.

For example,
with Django you can specify the Utterless test runner on the command line:

    $ ./manage.py test --testrunner utterless.contrib.django.DiscoverRunner

or by editing `settings.py` to contain:

    TEST_RUNNER = "utterless.contrib.django.DiscoverRunner"

Licence
-------

This software copyright P. S. Clarke and is licensed in accordance
with the BSD Three-Clause Licence.

Limitations and Roadmap
-----------------------

* Currently it completely ignores the `warnings` module,
so output from that
(e.g. a `DeprecationWarning` or a `ResourceWarning`)
will still splurts across the screen.
I could possibly collect that up during tests and include it
at the end.
The complication is that warnings should probably still be emited
regardless of whether the test passed or failed.
Treating warnings as errors might be the better option.


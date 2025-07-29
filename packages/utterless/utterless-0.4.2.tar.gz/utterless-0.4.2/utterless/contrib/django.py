

# Completely optional integration with the Django web framework


from django.test.runner import DiscoverRunner as DjangoDiscoverRunner

from utterless.runner import UtterlessTextTestRunner


class DiscoverRunner(DjangoDiscoverRunner):
    test_runner = UtterlessTextTestRunner

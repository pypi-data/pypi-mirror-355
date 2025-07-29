

from unittest.runner import TextTestRunner

from .results import UtterlessTextTestResult


class UtterlessTextTestRunner(TextTestRunner):

    def __init__(self, *args, **kwargs):
        kwargs["resultclass"] = UtterlessTextTestResult
        super().__init__(*args, **kwargs)

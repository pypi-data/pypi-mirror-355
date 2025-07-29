

import logging
import logging.handlers
from unittest.runner import TextTestResult


class CollectingHandler(logging.Handler):

    def __init__(self, record_list):
        logging.Handler.__init__(self)
        self.records = record_list

    def emit(self, record):
        self.records.append(record)

    def flush(self):
        pass


def try_to_format_as_line(formatter, record):
    try:
        return formatter.format(record)
    except Exception as exc:
        return "Utterless formatting error: %r raised %r" % (record, exc)


class UtterlessTextTestResult(TextTestResult):

    def startTest(self, test):
        super().startTest(test)
        self.old_level = logging.root.level
        self.old_handlers = logging.root.handlers
        logging.root.level = logging.DEBUG
        test.logHandler = CollectingHandler([])
        logging.root.handlers = [test.logHandler]

    def stopTest(self, test):
        logging.root.handlers = self.old_handlers
        logging.root.level = self.old_level
        super().stopTest(test)

    def printErrorList(self, flavour, errors):
        formatter = logging.Formatter(fmt=logging.BASIC_FORMAT)
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
            if hasattr(test, "logHandler") and test.logHandler.records:
                self.stream.writeln(self.separator2)
                for record in test.logHandler.records:
                    self.stream.writeln(try_to_format_as_line(formatter, record))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

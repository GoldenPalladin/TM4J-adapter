import logging
import traceback


class SplunkFormatter(logging.Formatter):
    """
    Class to create Splunk-compatible logs
    """
    def __init__(self, logging_app, project, reporter, fmt=None, datefmt=None, style='%', **extras):
        """

        :param logging_app: logger=
        :param project: project=
        :param reporter: reporter=
        :param fmt:
        :param datefmt:
        :param style:
        :param extras: any additional data to be added to Splunk event
        """
        self.project = project
        self.reporter = reporter
        self.logging_app = logging_app
        self.extras = extras
        super(SplunkFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record):

        def jsn(item: str) -> str:
            return str(item).replace('"', '\"')

        event = dict({'logger': self.logging_app,
                      'level': record.levelname,
                      'reporter': self.reporter,
                      'project': self.project,
                      'module': record.module,
                      'action': record.funcName,
                      'result': jsn(record.msg)})
        if self.extras:
            extras = {k: jsn(v) for (k, v) in self.extras.items()}
            event.update(extras)
        if record.exc_info:
            event.update({'traceback': ''.join(traceback.format_exception(*record.exc_info))})
        return event
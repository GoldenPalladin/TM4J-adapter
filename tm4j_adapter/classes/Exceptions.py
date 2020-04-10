class TM4JException(Exception):
    """Class for TM4J errors."""


class TM4JFolderNotFound(TM4JException):
    """No folder exists on search or creation"""


class TM4JInvalidFolderName(TM4JException):
    """No folder exists on search or creation"""


class TM4JObjectNotFound(TM4JException):
    """No testcase or step exists and autocreation is turned off"""


class TM4JInvalidValue(TM4JException):
    """Invalid value for parameters"""


class TM4JEnvironmentNotFound(TM4JException):
    """No environment exists"""
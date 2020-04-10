import logging

logger = logging.getLogger(__name__)


class TestParameters:
    """class to deal with test parameters
    """

    def __init__(self):
        self.parameters = {'variables': [], 'entries': []}
        self.variables = []
        self.entries = []

    def __setattr__(self, key, value):
        if key == 'variables':
            self.__dict__['variables'] = value
            self.__dict__['parameters']['variables'] = value
        elif key == 'entries':
            self.__dict__['entries'] = value
            self.__dict__['parameters']['entries'] = value
        else:
            self.__dict__[key] = value

    def set_variables(self, names: list):
        """
        initiate variables list
        :param names: list of parameter names
        """
        logger.debug(f'TP.set_variables: {names} to {self.parameters}')
        variables = list()
        for name in names:
            variables.append({'name': name, 'type': 'FREE_TEXT'})
        self.variables = variables

    def append_values(self, variables: list, values: list):
        """
        add parameter:value string
        :param variables: list of parameter names
        :param values: list of parameter values
        """
        logger.debug(f'TP.append_values: {values} to {self.parameters}')
        self.entries.append(dict(zip(variables, values)))

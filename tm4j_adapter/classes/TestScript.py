from classes.Exceptions import TM4JObjectNotFound
import configparser


class TestScript:
    """ class to deal with testscript created on test steps

    testScript json structure is created in self.script
    see https://docs.adaptavist.io/tm4j/server/api/v1/
"""

    def __init__(self, script=None):
        self.steps = []
        self.script = script if script else {'type': 'STEP_BY_STEP', 'steps': []}
        self.results = []
        self.__config = configparser.ConfigParser()
        self.__config.read('parseconfig.ini')

    def __setattr__(self, key, value):
        if key == 'script':
            self.__dict__['script'] = value
            if 'steps' in value:
                self.__dict__['steps'] = value['steps']
            else:
                self.__dict__['steps'] = []
        else:
            self.__dict__[key] = value

    def append_step(self, description: str, test_data: str, expected_result: str):
        """
        Appends step to steps list
        :param description: step description
        :param test_data: step test data
        :param expected_result: step expected result
         """
        self.steps.append({'testData': test_data, 'expectedResult': expected_result, 'description': description})
        self.script = {'type': 'STEP_BY_STEP', 'steps': self.steps}

    def get_step_id_index(self, description):
        filtered_steps = list(filter(lambda step: step['description'] == description, self.steps))
        return filtered_steps[0]['index'], filtered_steps[0]['id']

    def set_step_results(self, description: str, status: str, comment: str):
        """
        Finds step by name and set step execution result
        :param description: step name
        :param status: step execution ststus
        :param comment: execution comment
        """
        try:
            f_step = next((step for step in self.steps if step['description'] == description), None)
            f_step_index = self.steps.index(f_step)
            self.results.append({'index': f_step_index, 'status': status, 'comment': comment})
        except ValueError:
            if self.__config['NOTFOUND']['createStep'] == 'True':
                self.append_step(description, '', '')
                f_step_index = len(self.steps) - 1
                self.results.append({'index': f_step_index, 'status': status, 'comment': comment})
            else:
                raise TM4JObjectNotFound(
                    f'find_testcase: teststep {description} not found and auto-create is turned off')

    @classmethod
    def make_script_results(cls, script: dict, status: str) -> list:
        """
        Method to create script results from status
        :param script: testscript
        :param status: overall test status
        :return: scriptResults for post testresult
        """
        if script.get('steps'):
            if status == 'Pass':
                steps_amount = len(script.get('steps'))
                script_results = [{'index': ind, 'status': 'Pass', 'comment': ''} for ind in range(steps_amount)]
            elif status == 'Fail':
                script_results = [{'index': 0, 'status': 'Fail', 'comment': ''}]
            else:
                script_results = list()
            return script_results
        return list()



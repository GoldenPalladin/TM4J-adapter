"""
Library implements classes to upload test results to TM4J

Supposed usage sequence:
    tm4j = TM4J()                                               initialise objects
    ts = TestScript()
    tp = TestParameters()
    tm.find_testcase('testrun', "Test run name")
        for test in testsuite:
            tm.find_testcase('testcase', name, None, folder)    find_testcase a testcase by name
                                                                (will be created if none is found)
            ts = TestScript()
            if 'testScript' in tm.testcase:                     check if testcase already has steps
                ts.script = tm.testcase['testScript']           read it
            table = test_data_source                            get test data (i.e. from scenario outline)
            tp.set_variables(table.headings)                    initialise data variables
            for row in table.rows:
                tp.append_values(row.headings, row.cells)       add variable:value pairs
            testcase.update({'parameters': tp.parameters})
            for step in steps:  
                ts.set_step_results(name, status, comment)      add steps to test script
            tm.testcase['testScript'] = ts.script               
            tm.update_testcase(updated_values)                  update testcase
            tm.post_test_result('Pass', tm.config['RESULTS']['env'], tm.config['RESULTS']['reporter'], ts.results)
"""

import json
import urllib3
import logging.config
import re
import configparser
from os import path
from requests import Session, Request, Response
from tm_log import LOG_CONFIG

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('tmconnect')
csv_logger = logging.getLogger('tmconnectCSV')
s_logger = logging.getLogger('tmconnectSplunk')


def _strip_none_values(obj):
    """constructs json from object without Null values"""
    try:
        name = obj['name'].replace("'", "").replace('"', '')
        obj.update({'name': name})
    except KeyError:
        pass
    finally:
        return json.dumps({k: v for k, v in obj.items() if v is not None})


def _check_parameter(value, true_result, false_result=None):
    """Some logic to shortify code"""
    if value:
        return true_result
    elif false_result:
        return false_result
    else:
        return ''


def _splunk_format(project: str, action: str, itemkey: str, result: str, url: str, **details) -> str:
    """returns json-string in Splunk log format"""
    log_string = dict({'logger': 'tm4j_adapter',
                       'project': project,
                       'action': action,
                       'itemkey': itemkey,
                       'result': result,
                       'url': url})
    if details:
        log_string.update(details)
    return json.dumps(log_string)


def _validate_script_results_json(script: list) -> list:
    """filter unwanted keys in script results"""
    keys = ['index', 'status', 'comment']
    result = []
    for step in script:
        result.append(dict([(i, step[i]) for i in step if i in set(keys)]))
    return result


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


def _check_error_response(response: Response):
    """function checks for Folder errors"""
    if response.status_code == 400:
        if bool(re.search(r".+not found for field folder.+", response.text)):
            raise TM4JFolderNotFound(f'{response.text}')
        if bool(re.search(r".+folder should start with a slash.+", response.text)):
            raise TM4JInvalidFolderName(f'{response.text}')
        if bool(re.search(r".+was not found for field environment.+", response.text)):
            raise TM4JInvalidValue(f'{response.text}')


class TM4J:
    """Class containing all values for testcase or test run and methods for managing them"""

    def __init__(self):

        self.config = configparser.ConfigParser()
        self.config.read(path.join(path.abspath(path.dirname(__file__)), 'parseconfig.ini'))
        self.__baseurl = self.config['GENERAL']['tm4jUrl']
        self.__serviceurl = self.__baseurl.replace("atm", "tests")
        self.__login = self.config['GENERAL']['tm4jLogin']
        self.__password = self.config['GENERAL']['tm4jPassword']
        self.project_key = self.config['GENERAL']['tm4jProjectKey']
        self.__session = Session()
        self.__session.auth = (self.__login, self.__password)
        self.__testResultsId = None
        self.testcase = None
        self.__tc_internal_id = None
        self.testrun = None
        self.__init_testcase()
        self.__init_testrun()

    def __init_testcase(self):
        """ clears all testcase attributes"""
        self.testcase = {'projectKey': self.project_key, 'key': None, 'name': None, 'priority': 'Normal',
                         'folder': None, 'status': None, 'labels': None, 'testScript': None, 'issueLinks': None}

    def __init_testrun(self):
        """clears all testrun attributes"""
        self.testrun = {'projectKey': self.project_key, 'key': None, 'name': None, 'folder': None}

    def __do(self, method: str, url: str, payload, isfile: bool = False) -> json:
        """General method to perform HTTP-actions"""
        logger.debug(f"HTTP action called with params: {locals()}...")
        if isfile:
            r = Request(method, url, None, payload, None, None, self.__session.auth)
        else:
            headers = {'Content-Type': 'application/json', 'Content-Length': str(len(payload.encode('utf-8')))}
            r = Request(method, url, headers, None, str(payload), None, self.__session.auth)
        prep_req = self.__session.prepare_request(r)
        do_response = self.__session.send(prep_req, verify=False)
        logger.debug(f'_do response: {do_response.content}')
        _check_error_response(do_response)
        do_response.raise_for_status()
        if do_response.text:
            response_json = do_response.json()
        else:
            response_json = ''
        return response_json

    def _get_tc_id(self):
        """
        Function to get internal tc id
        :return:
        """
        if self.testcase["key"]:
            url = f'{self.__serviceurl}/testcase/{self.testcase["key"]}?fields=id'
            payload = ''
            self.__tc_internal_id = self.__do('get', url, payload)['id']
        else:
            raise TM4JInvalidValue('Testcase key not set, find testcase first')

    def add_weblink(self, link_url: str, description: str):
        """
        Add weblink to traceability tab
        :param link_url:
        :param description:
        :return:
        """
        if self.__tc_internal_id:
            url = f'{self.__serviceurl}/tracelink/bulk/create'
            payload = json.dumps([{"url": link_url,
                                   "urlDescription": description,
                                   "testCaseId": self.__tc_internal_id,
                                   "typeId": 1}])
            self.__do('post', url, payload)
        else:
            raise TM4JInvalidValue('Testcase internal id not set, find testcase first')

    def find_testcase(self, name: str, key: str = None, folder: str = None):
        """Search method for test run or test cases. If no result found, new item is created.
        Found testcase is stored in self parameter.
        :param name: name of the item to search
        :param key: if specified, search by key only, name is ignored
        :param folder: if specified, search in folder; if no item found, it will be created in this folder.
            Folder should be specified in "parent folder" or "parent folder/child folder" format
        """
        logger.debug(f"Find testcase with params: {locals()}")
        name = name.replace("'", "").replace('"', '')
        if name == '':
            raise TM4JInvalidValue('Testcase name cannot be empty!')
        folder = _check_parameter(folder, folder, self.config['GENERAL']['tcFolder'])
        if not folder.isalnum():
            raise TM4JInvalidFolderName(f"Folder '{folder}' must have alphanumeric name!")
        url_options = list()
        url_options.append(f'{self.__baseurl}/testcase/search?version=1.0&maxResults=10&query=')
        url_options.append(_check_parameter(key, f' key = "{key}"', f' projectKey = "{self.project_key}" AND name ~ "{name}"'))
        url_options.append(_check_parameter(key, '', f" AND folder = \"/{folder}\""))
        url = ''.join(url_options)
        payload = ''
        try:
            response = self.__do('get', url, payload)
            self.testcase = response[0]
            self._get_tc_id()
        except IndexError:
            if name:
                self.__post_new_testcase(name, folder)
            else:
                raise TM4JObjectNotFound(f'find_testcase: testcase {key} not found and name is not specified')
        except TM4JFolderNotFound:
            self.__create_folder('TEST_CASE', folder)
            self.__post_new_testcase(name, folder)

    def __post_new_testcase(self, name: str, folder: str):
        """creates new testcase from self.testcase.
        :return nothing, but updates self.testcase"""
        if self.config['NOTFOUND']['createTestcase'] == 'True':
            logger.debug(f"Post testcase with params: {locals()}")
            self.__init_testcase()
            self.testcase['name'] = name
            self.testcase['folder'] = f"/{folder}"
            self.testcase['status'] = 'Approved'
            key = self.post_testcase_from_json(self.testcase)
            url = f'{self.__baseurl}/testcase'
            self.testcase = self.__do('get', url + '/' + key, '')
            logger.info(f"Testcase posted successfully. {self.testcase}")
        else:
            self.__init_testcase()
            raise TM4JObjectNotFound(f'find_testcase: testcase {name} not found and auto-create is turned off')

    def update_testcase(self, updated_values: json):
        """update testcase from self parameters"""
        url = f'{self.__baseurl}/testcase/{self.testcase["key"]}'
        testcase = {
            'name': updated_values['name'],
            'objective': updated_values.get('objective', None),
            'precondition': updated_values.get('precondition', None),
            'status': updated_values['status'],
            'priority': updated_values.get('priority', None),
            'owner': updated_values.get('owner', None),
            'estimatedTime': updated_values.get('estimatedTime', None),
            'component': updated_values.get('component', None),
            'labels': updated_values.get('labels', None),
            'folder': updated_values['folder'],
            'issueLinks': updated_values.get('issueLinks', None),
            'customFields': updated_values.get('customFields', None),
            'parameters': updated_values.get('parameters', None),
            'testScript': {'type': 'STEP_BY_STEP', 'steps':
                           [{k: v for k, v in d.items() if k != 'index'}
                            for d in updated_values.get('testScript', [])['steps']]}
        }
        self.__do('put', url, payload=_strip_none_values(testcase))

    def post_testcase_from_json(self, testcase: json) -> str:
        """creates testcase directly from json
        :param testcase: json-formatted testcase. See https://docs.adaptavist.io/tm4j/server/api/v1/
        :return testcase key"""
        url = f'{self.__baseurl}/testcase'
        tc_key = None
        if testcase['name'] == '':
            raise TM4JInvalidValue('Testcase name cannot be empty!')
        try:
            tc_key = self.__do('post', url, payload=_strip_none_values(testcase))['key']
        except TM4JFolderNotFound:
            self.__create_folder('TEST_CASE', testcase['folder'])
            tc_key = self.__do('post', url, payload=_strip_none_values(testcase))['key']
        finally:
            self.testcase['key'] = tc_key
            self._get_tc_id()
            csv_logger.info(f'{tc_key}, {testcase["name"]}')
            logger.info(f'Testcase {tc_key} created successfully.')
            s_logger.info(_splunk_format(self.project_key, 'Create Testcase', tc_key, 'Success', f'{url}/{tc_key}'))
            return tc_key

    def __create_folder(self, folder_type: str, name: str):
        """function creates folder of specified type"""
        url = f'{self.__baseurl}/folder'
        if (self.config['NOTFOUND']['createTcFolder'] == 'True' and folder_type == 'TEST_CASE') \
                or (self.config['NOTFOUND']['createTrFolder'] == 'True' and folder_type == 'TEST_RUN'):
            folder = {"projectKey": self.project_key, "name": f'/{name}', "type": folder_type}
            self.__do('post', url, payload=_strip_none_values(folder))
        else:
            raise TM4JObjectNotFound(
                f'find_testcase/testrun: {folder_type} folder "{name}" is not found and auto-create is turned off')

    def find_testrun(self, name: str, folder: str = None):
        """Search method for one or more test cycles. Search by testcycle name. If no result found, new item is created.
        Found testcycle is stored in self parameter
        :param name: name of the item to search
        :param folder: if specified, search in folder;
        if no item found, it will be created in this folder.
        If None, config folder will be used
            Folder should be specified in "parent folder" or "parent folder/child folder" format
        """
        logger.debug(f"Find testcase with params: {locals()}")
        folder = _check_parameter(folder, folder, self.config['GENERAL']['trFolder'])
        if not folder.isalnum():
            raise TM4JInvalidFolderName(f"Folder '{folder}' must have alphanumeric name!")
        url_options = list()
        url_options.append(f'{self.__baseurl}/testrun')
        url_options.append(f'/search?version=1.0&maxResults=10&query=projectKey = "{self.project_key}"')
        url_options.append(f" AND folder = \"/{folder}\"")
        url = ''.join(url_options)
        payload = ''
        try:
            response = self.__do('get', url, payload)
            testruns = list(filter(lambda testrun: testrun['name'] == name, response))
            self.testrun = testruns[0]
        except IndexError:
            self.post_new_testrun(name, folder, None, True)
        except TM4JFolderNotFound:
            self.__create_folder('TEST_RUN', folder)
            self.post_new_testrun(name, folder, None, True)

    def post_new_testrun(self, name: str, folder: str = None, linked_issue: str = None, check_config: bool = False):
        """
        Creates new testcycle. Created testcycle is stored in self.testrun parameter
        :param name: testcycle name
        :param folder: testcycle folder. If None, config folder will be used
        :param linked_issue: linked Jira issue
        :param check_config: is passed from find_testrun method to check if
        auto creation of not-found is allowed
        """
        logger.debug(f"Post testrun with params: {locals()}")
        if self.config['NOTFOUND']['createTestrun'] != 'True' and check_config:
            raise TM4JObjectNotFound(f'find_testrun: TestCycle {name} not found and auto-create is turned off')
        else:
            url = f'{self.__baseurl}/testrun'
            key = None
            folder = _check_parameter(folder, folder, self.config['GENERAL']['trFolder'])
            if not folder.isalnum():
                raise TM4JInvalidFolderName(f"Folder '{folder}' must have alphanumeric name!")
            self.__init_testrun()
            self.testrun['name'] = name
            if linked_issue:
                self.testrun['issueKey'] = linked_issue[0]
            self.testrun['folder'] = f"/{folder}"
            try:
                key = self.__do('post', url, payload=_strip_none_values(self.testrun))['key']
            except TM4JFolderNotFound:
                self.__create_folder('TEST_RUN', folder)
                key = self.__do('post', url, payload=_strip_none_values(self.testrun))['key']
            finally:
                self.testrun = self.__do('get', url + '/' + key, '')
                logger.info(f"Testrun {self.testrun['key']} created successfully.")
                s_logger.info(_splunk_format(self.project_key, 'Create Testcycle', self.testrun['key'], 'Success',
                                             f'{url}/{self.testrun["key"]}'))

    def post_test_result(self, status: str, environment: str, executed_by: str, script_results: json = None, comment: str = None):
        """
        Creates test execution result in current testcycle and testcase for specified status, executor and env
        :param status: testcase execution status. Auto set to Fail if any step is Fail.
        :param environment: env parameter. Must correspond to one in TM4J settings
        :param executed_by: name of person executed tests
        :param script_results: json with steps execution results
        :param comment: comment to testcase execution
        """
        if self.testrun['key'] is None:
            message = 'post_test_result: no testrun id found, call _post_new_testrun first'
            logger.debug(message)
            raise TM4JException(message)
        elif self.testcase['key'] is None:
            message = 'post_test_result: no testcase id found, call find_testcase("testcase", name)  first'
            logger.debug(message)
            raise TM4JException(message)
        else:
            if script_results:
                script_results = _validate_script_results_json(script_results)
                status = "Fail" if (list(filter(lambda step: step['status'] == "Fail", script_results))) else status
            payload = _strip_none_values({"status": status, "environment": environment,
                                          "comment": comment, "executedBy": executed_by, "scriptResults": script_results})
            url = f'{self.__baseurl}/testrun/{self.testrun["key"]}/testcase/{self.testcase["key"]}/testresult'
            response = self.__do('post', url, payload)
            self.__testResultsId = response['id']
            logger.info(f'Test results posted successfully. Testcase:{self.testcase["key"]}, \\n\\rResults:{payload}')

            s_logger.info(_splunk_format(self.project_key, 'Testcase execution', self.testcase['key'],
                                         status, f'{self.__baseurl}/testrun/{self.testrun["key"]}/testresults',
                                         **{'env': environment, 'executed by': executed_by, 'testcycle': self.testrun['key']}))

    def attach_testrun_file(self, file_path: str):
        """
        Attach file to TestCycle execution. Must have value of *self.testrun['key']*
        -- create TestCycle beforehand.
        :param file_path:
        :return:
        """
        if self.testrun['key'] is not None:
            payload = {'file': open(file_path, 'rb')}
            url = f'{self.__baseurl}/testrun/{self.testrun["key"]}/attachments'
            self.__do('post', url, payload, True)
            logger.debug(f'Attached file to testcycle {self.testrun["key"]}')
        else:
            raise TM4JException('attachTestResultFile: no testCycle id exists, call post_new_testrun first')

    def attach_testcase_result_file(self, file_path: str):
        """Attach file to TestCase execution. Must have value of *self.__testResultsId*
-- call post_new_testrun beforehand."""
        if self.__testResultsId is not None:
            payload = {'file': open(file_path, 'rb')}
            url = f'{self.__baseurl}/testresult/{str(self.__testResultsId)}/attachments'
            self.__do('post', url, payload, True)
            logger.debug(f'Attached file to testcase {self.testcase["key"]}')
        else:
            raise TM4JException('attachTestResultFile: no testResult id exists, call postTestResults first')

    @property
    def test_id(self):
        return self.testcase['key']


class TestScript:
    """ class to deal with testscript created on test steps

    testScript json structure is created in self.script
    see https://docs.adaptavist.io/tm4j/server/api/v1/
"""

    def __init__(self):
        self.steps = []
        self.script = {'type': 'STEP_BY_STEP', 'steps': []}
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

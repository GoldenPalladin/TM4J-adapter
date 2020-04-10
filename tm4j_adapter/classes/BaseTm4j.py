import json
import urllib3
import re
from typing import List
from requests import Session, Request, Response
from libs.tm_log import csv_logger, get_logger
from libs.config import read_config
from libs.tags_parse_lib import is_jira_issue, strip_none_values, choose, check_folder_name, is_true
from classes.Exceptions import TM4JObjectNotFound, TM4JInvalidValue, TM4JFolderNotFound, TM4JInvalidFolderName, \
    TM4JException, TM4JEnvironmentNotFound

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _check_error_response(response: Response):
    """function checks for Folder errors"""
    text = f'Status {response.status_code} for URL {response.url}. Details: "{response.text}. ' \
        f'Request: {response.request.body}"'
    if response.status_code == 400:
        if bool(re.search(r".+not found for field folder.+", response.text)):
            raise TM4JFolderNotFound(f'{text}')
        if bool(re.search(r".+folder should start with a slash.+", response.text)):
            raise TM4JInvalidFolderName(f'{text}')
        if bool(re.search(r".+was not found for field environment on project+", response.text)):
            raise TM4JEnvironmentNotFound(f'{text}')
        if bool(re.search(r".+was not found for field+", response.text)):
            raise TM4JInvalidValue(f'{text}')
    elif response.status_code == 404:
        raise TM4JObjectNotFound(f'{text}')
    elif response.status_code == 500:
        raise TM4JException(f'{text}')


class BaseTm4j:
    """
    base class to manage TM4J API with all connection logic and service functions
    """
    def __init__(self, config_path=None):
        self.config = read_config(config_path)
        self._baseurl = self.config['GENERAL']['tm4jUrl']
        self._serviceurl = self._baseurl.replace("atm", "tests")
        self._jira_url = self._baseurl.replace('atm/1.0', 'api/2')
        self._login = self.config['GENERAL']['tm4jLogin']
        self._password = self.config['GENERAL']['tm4jPassword']
        self.project_key = self.config['GENERAL']['tm4jProjectKey']
        self.logger = get_logger(__name__, self.config)
        self._session = Session()
        self._session.auth = (self._login, self._password)
        self._testResultsId = None
        self.testcase = None
        self._tc_internal_id = None
        self.testrun = None
        self._tr_internal_id = None
        self._init_testcase()
        self._init_testrun()

        url = f'{self._serviceurl}/project'
        projects = self._do('get', url, '')

        self._tc_project_id = int([x for x in projects if x['key'] == self.project_key][0]['id'])

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        return False

    def _init_testcase(self):
        """ clears all testcase attributes"""
        self.testcase = {'projectKey': self.project_key, 'key': None, 'name': None, 'priority': 'Normal',
                         'folder': None, 'status': None, 'labels': None, 'testScript': None, 'issueLinks': None}
        self._tc_internal_id = None

    def _init_testrun(self):
        """clears all testrun attributes"""
        self.testrun = {'projectKey': self.project_key, 'key': None, 'name': None, 'folder': None, 'owner': None}
        self._tr_internal_id = None

    def _do(self, method: str, url: str, payload, isfile: bool = False, expect_response: bool = False):
        """General method to perform HTTP-actions"""
        self.logger.debug(f"HTTP action called with params: {locals()}...")
        if isfile:
            r = Request(method, url, None, payload, None, None, self._session.auth)
        else:
            headers = {'Content-Type': 'application/json', 'Content-Length': str(len(str(payload).encode('utf-8')))}
            r = Request(method, url, headers, None, str(payload), None, self._session.auth)
        prep_req = self._session.prepare_request(r)
        for i in range(3):
            do_response = self._session.send(prep_req, verify=False)
            self.logger.debug(f'_do response: {do_response.content}')
            _check_error_response(do_response)
            try:
                do_response.raise_for_status()
            except Exception as e:
                self.logger.exception(e)
                raise e
            if not do_response.text and expect_response:
                self.logger.info(f'Results expected, retrying to get it')
                continue
            else:
                result = do_response.json() if do_response.text else ''
                return result
        self.logger.error(f'Max retries exceeded')
        return ''

    def _get_tc_id(self) -> str:
        """
        Function to get internal testcase id and project id
        :return:
        """
        key = self.testcase["key"]
        if key:
            url = f'{self._serviceurl}/testcase/{key}?fields=id,projectId'
            payload = ''
            response = self._do('get', url, payload, False, True)
            self.logger.debug(f'{key} - {response}')
            self._tc_internal_id = response['id']
            return response['id']
        else:
            raise TM4JInvalidValue('Testcase key not set, find testcase first')

    def _get_tr_id(self):
        """
        Function to get internal testcase id and project id
        :return:
        """
        key = self.testrun["key"]
        if key:
            url = f'{self._serviceurl}/testrun/{key}?fields=id,projectId'
            payload = ''
            response = self._do('get', url, payload, False, True)
            self.logger.debug(f'{key} - {response}')
            self._tr_internal_id = response['id']
            return self._tr_internal_id
        else:
            raise TM4JInvalidValue('Testrun key not set, find testrun first')

    def _get_jira_issue_id(self, issue_key: str) -> str:
        """
        function to get jira internal issue id from key
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/?_ga=2.70345104.1045553653.1576580663-1887700939.1576580663#api-rest-api-3-issue-issueIdOrKey-get
        :param issue_key:
        :return:
        """
        url = f'{self._jira_url}/issue/{issue_key}'
        payload = ''
        try:
            response = self._do('get', url, payload)
            return response['id']
        except Exception as e:
            self.logger.exception(f'{e}')

    def _put_testcase_paramtype_property(self):
        """
        some magic to display TestData table in UI without manual switch&save
        :return:
        """
        if self.testcase.get('parameters', None):
            self._get_tc_id()
            payload = {"id": self._tc_internal_id,
                       "projectId": self._tc_project_id,
                       "paramType": "TEST_DATA",
                       "parameters": []}
            url = f'{self._serviceurl}/testcase/{self._tc_internal_id}'
            self._do('put', url, payload=strip_none_values(payload))
            self.logger.debug(f'Success!')

    def _create_folder(self, folder_type: str, name: str):
        """function creates folder of specified type"""
        self.logger.info(f'Creating new {folder_type} folder {name}')
        url = f'{self._baseurl}/folder'
        if (is_true(self.config['NOTFOUND']['createTcFolder']) and folder_type == 'TEST_CASE') \
                or (is_true(self.config['NOTFOUND']['createTrFolder']) and folder_type == 'TEST_RUN'):
            folder = {"projectKey": self.project_key, "name": f'/{name}', "type": folder_type}
            self._do('post', url, payload=strip_none_values(folder))
        else:
            raise TM4JObjectNotFound(
                f'find_testcase/testrun: {folder_type} folder "{name}" is not found and auto-create is turned off')

    def _check_environment(self, env: str) -> str:
        """
        Function checks current environments in the project and returns case-sensitive name
        or creates a new one. It seems that when posting results, environment is case-sensitive
        (so qas != QAS and TM4JEnvironmentNotFound exception is raised), but environment creation
        is case insensitive (so trying to create qas when there is QAS leads to API error)
        so we have to do all this magic
        """
        self.logger.info(f' Got env name error. Checking if env {env} already exists in system.')
        url = f'{self._baseurl}/environments'
        existing_environments: List[dict] = self._do('get', f'{url}?projectKey={self.project_key}', None)
        for current_env in existing_environments:
            current_env_name: str = current_env.get('name')
            if current_env_name.lower() == env.lower():
                self.logger.error(f'Environment name is case-sensitive! '
                             f'Fix your config EXECUTION.env = {env} to {current_env_name} '
                             f'to avoid extra checks')
                return current_env_name
        self.logger.info(f' Creating new env: {env}')
        payload = {"projectKey": self.project_key,
                   "name": env,
                   "description": "Created by TM4J"}
        self.logger.debug(f'url: {url}, payload: {payload}')
        self._do('post', url, payload=strip_none_values(payload))
        return env

    def _add_testcycle_jira_link(self, linked_issues: str):
        self.logger.debug(locals())
        linked_issues_list = list(map(lambda x: x.strip(), linked_issues.split(',')))
        if len(linked_issues_list) == 0:
            raise TM4JInvalidValue('Jira issues list is empty')
        tr_id = self._get_tr_id()
        payload = list()
        for issue in linked_issues_list:
            if is_jira_issue(issue):
                payload.append({'testRunId': tr_id,
                                'issueId': self._get_jira_issue_id(issue),
                                'typeId': 2})
        url = f'{self._serviceurl}/tracelink/bulk/create'
        if payload:
            self._do('post', url, strip_none_values(payload))

    def _delete_testrun(self, key):
        """
        for testing use
        :param key: existing testcase key
        :return:
        """
        url = f'{self._baseurl}/testrun/{key}'
        self._do('delete', url, '')
        self.logger.info(f'Testrun {key} deleted')

    def _delete_testcase(self, key: str):
        """
        for testing use
        :param key: existing testcase key
        :return:
        """
        url = f'{self._baseurl}/testcase/{key}'
        self._do('delete', url, '')

    def _post_new_testcase(self,
                           name: str,
                           folder: str,
                           test_source_file_path: str = ''):
        """creates new testcase from self.testcase.
        :param test_source_file_path: additional logging parameters about testcase creation for csv self.logger
        :return nothing, but updates self.testcase"""
        self.logger.debug(f"Post testcase with params: {locals()}")
        key = None
        self._init_testcase()
        self.testcase['name'] = name
        self.testcase['folder'] = f"/{folder}"
        self.testcase['status'] = 'Approved'
        url = f'{self._baseurl}/testcase'
        if name == '':
            raise TM4JInvalidValue('Testcase name cannot be empty!')
        response: dict = self._do('post', url, payload=strip_none_values(self.testcase))
        key = response['key']
        csv_log_data = [key, name, test_source_file_path]
        csv_logger.info('#'.join(csv_log_data))
        self.logger.info(f'Testcase {key} created successfully.')
        #  now load full data of created testcase
        url = f'{self._baseurl}/testcase/{key}'
        self.testcase = self._do('get', url, '')
        self._get_tc_id()
        self.logger.info(f"Testcase posted successfully. {self.testcase}")

    def _post_new_testcycle(self,
                            name: str,
                            folder: str = None,
                            linked_issues: str = None,
                            check_config: bool = False,
                            executor: str = None):
        """
        Creates new testcycle. Created testcycle is stored in self.testrun parameter
        :param name: testcycle name
        :param folder: testcycle folder. If None, config folder will be used
        :param linked_issues: linked Jira issues list
        :param check_config: is passed from find_testcycle method to check if
        :param executor: name of the testcycle owner
        auto creation of not-found is allowed
        """
        self.logger.info(f"Post testrun with params: {locals()}")
        if self.config['NOTFOUND']['createTestrun'] != 'True' and check_config:
            raise TM4JObjectNotFound(f'find_testcycle: TestCycle {name} not found and auto-create is turned off')
        else:
            url = f'{self._baseurl}/testrun'
            key = None
            folder = choose(folder, folder, self.config['GENERAL']['trFolder'])
            check_folder_name(folder)
            self._init_testrun()
            self.testrun['name'] = name
            self.testrun['owner'] = executor
            self.testrun['folder'] = f"/{folder}"
            try:
                key = self._do('post', url, payload=strip_none_values(self.testrun))['key']
            except TM4JFolderNotFound:
                self._create_folder('TEST_RUN', folder)
                key = self._do('post', url, payload=strip_none_values(self.testrun))['key']
            finally:
                self.testrun = self._do('get', url + '/' + key, '')
                if linked_issues:
                    self._add_testcycle_jira_link(linked_issues)
                self.logger.info(f"Testrun {key} created successfully.")
                return key

    def _get_testcase_run_id(self, key: str) -> tuple:
        """
        Function to get internal run id for testcase added into testcycle
        :param key: testcase key
        :return:
        """
        self._get_tr_id()
        url = f'{self._serviceurl}/testrun/{self._tr_internal_id}/testrunitems' \
            f'?fields=id,index,issueCount,$lastTestResult'
        response = self._do('get', url, '')
        for item in response:
            if item['$lastTestResult']['testCase']['key'] == key:
                return item['id'], item['$lastTestResult']['id']
        raise TM4JObjectNotFound(f'Cannot find {key} run id in testrun {self._tr_internal_id}')

    def _put_update_secript_status(self, run_id):
        """
        Some tm4j api magic: testcase with parameters table that was added on
        /testrun/{testRunKey}/testcase/{testCaseKey}/testresult
        shows testscript as outdated, so we have to update it
        :param run_id: testcase run id in testcycle
        :return:
        """
        url = f'{self._serviceurl}/testresult/{run_id}/updatetestscripts'
        payload = f'{{"id":{run_id}}}'
        self._do('put', url, payload)

    def _get_datarow_ids(self, run_id: str) -> dict:
        """
        Function to get list of parameterset ids (datarow ids) - in order to post DD executions
        :param run_id: testcase run id.
        :return: list of row id of the last (current) executions
        """
        url = f'{self._serviceurl}/testrun/{self._tr_internal_id}/testresults?fields=id,testResultStatusId,' \
            f'testScriptResults(id,testResultStatusId,comment,index,sourceScriptType,parameterSetId),' \
            f'traceLinks&itemId={run_id}'
        last_execution = self._do('get', url, '')
        if last_execution:
            result = dict()
            for item in last_execution[0]['testScriptResults']:
                parameterset_id = item.get('parameterSetId', None)
                # parameterSetId = row x in test data table, so it should exists
                if parameterset_id:
                    step_ids_list = result.get(parameterset_id, None)
                    if step_ids_list:
                        step_ids_list.append(item['id'])
                    else:
                        result.update({parameterset_id: [item['id']]})
            if len(result) == 0:
                raise TM4JObjectNotFound(f'No data table rows found for run_id {run_id}')
            return {k: result[k] for k in sorted(result)}
        else:
            raise TM4JInvalidValue(f'No execution results are found for {run_id}')

    def _put_testscript_results(self, script_results: str):
        """
        Function to post testcase rows execution results
        :param script_results: json (step execution id, result id, executed)
        :return:
        """
        url = f'{self._serviceurl}/testscriptresult/'
        self._do('put', url, payload=script_results)

    def get_project_testresult_status_codes(self) -> json:
        """
        function to get project UI execution status codes
        :return:
        [{isDefault: true,  name: "Not Executed", id: 927, projectId: 17603},
         {isDefault: false,  name: "Pass", id: 929, projectId: 17603}, ...]
        """
        url = f'{self._serviceurl}/project/{self._tc_project_id}/testresultstatus/'
        payload = ''
        try:
            response = self._do('get', url, payload)
            return response
        except Exception as e:
            self.logger.exception(f'{e}')





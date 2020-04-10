import json
from classes.DataStructures import TestCaseExecution
from classes.TestScript import TestScript
from libs.tags_parse_lib import split_testcase_name_key, clear_name, \
    strip_none_values, choose, validate_script_results_json, check_folder_name, is_true
from classes.BaseTm4j import BaseTm4j
from classes.Exceptions import TM4JObjectNotFound, TM4JInvalidValue, \
    TM4JFolderNotFound, TM4JException, TM4JEnvironmentNotFound


class TM4J(BaseTm4j):
    """Class to manage testcase and testcycle (find, post executions, attach files"""
    def __init__(self, config_path=None):
        super().__init__(config_path)

    def find_testcase(self,
                      name: str = None,
                      key: str = None,
                      folder: str = None,
                      test_source_file_path: str = '',
                      autocreate: bool = False) -> str:
        """Search method for test run or test cases. If no result found, new item is created.
        Found testcase is stored in self parameter.
        :param name: name of the item to search
        :param key: if specified, search by key only, name is ignored
        :param folder: if specified, search in folder; if no item found, it will be created in this folder.
            Folder should be specified in "parent folder" or "parent folder/child folder" format
        :param test_source_file_path: test source path for csv logger
        :param autocreate: option to override tests autocreation
        """
        autocreate = autocreate or is_true(self.config['NOTFOUND']['createTestcase'])
        self.logger.debug(f"Find testcase with params: {locals()}")
        url_options = list()
        url_options.append(f'{self._baseurl}/testcase/search?version=1.0&maxResults=10&query=')
        if key:
            url_options.append(f' key = "{key}"')
        else:
            name = clear_name(name)
            if name == '':
                raise TM4JInvalidValue('Testcase name cannot be empty!')
            n_key, n_name = split_testcase_name_key(name, self.config['GENERAL']['testCaseKeyDelimiter'])
            # check if name starts with testCase key -- then find by key
            if n_key:
                self.find_testcase(n_name, n_key, folder, test_source_file_path)
                return self.testcase['key']
            else:
                folder = choose(folder, folder, self.config['GENERAL']['tcFolder'])
                check_folder_name(folder)
                url_options.append(f' projectKey = "{self.project_key}" AND name = "{name}"')
                url_options.append(choose(folder, f" AND folder = \"/{folder}\"", ''))
        url = ''.join(url_options)
        payload = ''
        try:
            response = self._do('get', url, payload, False, True)
            self.testcase = response[0]
            self._get_tc_id()
        except IndexError:
            if autocreate and name:
                self.logger.info(f'Cannot find testcase {key} - {name}. Will create a new one')
                self._post_new_testcase(name, folder, test_source_file_path)
            else:
                msg = f'find_testcase: testcase {key} not found. '\
                      f'Name=\"{name}\" or autocreate={autocreate} do not allow creation'
                self.logger.exception(msg)
                raise TM4JObjectNotFound(msg)
        except TM4JFolderNotFound:
            self._create_folder('TEST_CASE', folder)
            self._post_new_testcase(name, folder, test_source_file_path)
        return self.testcase['key']

    def update_testcase(self, updated_values: json):
        """update testcase from self parameters"""
        url = f'{self._baseurl}/testcase/{self.testcase["key"]}'
        folder = updated_values['folder'] if updated_values['folder'][0] == '/' \
            else f"/{updated_values['folder']}"
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
            'folder': folder,
            'parameters': updated_values.get('parameters', None),
            'issueLinks': updated_values.get('issueLinks', None),
            'customFields': updated_values.get('customFields', None),
            'testScript': {'type': 'STEP_BY_STEP', 'steps':
                           [{k: v for k, v in d.items() if k != 'index'}
                            for d in updated_values.get('testScript', [])['steps']]}
        }
        try:
            self._do('put', url, payload=strip_none_values(testcase))
        except TM4JFolderNotFound:
            self._create_folder('TEST_CASE', folder.strip('/'))
            self._do('put', url, payload=strip_none_values(testcase))
        finally:
            self._put_testcase_paramtype_property()

    def add_testcase_weblink(self, link_url: str, description: str):
        """
        Add weblink to testcase traceability tab
        :param link_url:
        :param description:
        :return:
        """
        if not self._tc_internal_id:
            raise TM4JInvalidValue('Testcase internal id not set, find testcase first')
        url = f'{self._serviceurl}/tracelink/bulk/create'
        payload = json.dumps([{"url": link_url,
                               "urlDescription": description,
                               "testCaseId": self._tc_internal_id,
                               "typeId": 1}])
        try:
            self._do('post', url, payload)
        except TM4JInvalidValue:
            pass

    def find_testcycle(self,
                       name: str = None,
                       folder: str = None,
                       key: str = None,
                       linked_issues: str = None,
                       executor: str = None):
        """Search method for one or more test cycles. Search by testcycle name. If no result found, new item is created.
        Found testcycle is stored in self parameter
        :param name: name of the item to search
        :param folder: if specified, search in folder;
        :param key: TestCycle key to search
        :param linked_issues: list of Jira issues for new testCycle
        :param executor: testCycle owner for new testCycle
        if no item found, it will be created in this folder.
        If None, config folder will be used
            Folder should be specified in "parent folder" or "parent folder/child folder" format
        """
        self.logger.info(f"Find testrun with params: {locals()}")
        payload = ''
        url_options = list()
        url_options.append(f'{self._baseurl}/testrun/search?version=1.0&maxResults=10&query=')
        if key:
            url_options.append(f' key = "{key}"')
            url = ''.join(url_options)
            response = self._do('get', url, payload)
            self.testrun = response[0]
        else:
            name = choose(name, name, self.config['EXECUTION']['testcycleName'])
            folder = choose(folder, folder, self.config['GENERAL']['trFolder'])
            check_folder_name(folder)
            url_options.append(f'projectKey = "{self.project_key}"')
            url_options.append(f" AND folder = \"/{folder}\"")
            url = ''.join(url_options)
            try:
                response = self._do('get', url, payload)
                testruns = list(filter(lambda testrun: testrun['name'] == name, response))
                self.testrun = testruns[0]
            except IndexError:
                self._post_new_testcycle(name, folder, linked_issues, True, executor)
            except TM4JFolderNotFound:
                self._create_folder('TEST_RUN', folder)
                self._post_new_testcycle(name, folder, linked_issues, True, executor)
        return self.testrun['key']

    def post_test_result(self, status: str,
                         environment: str,
                         executed_by: str,
                         script_results: json = None,
                         comment: str = None,
                         test_cycle_key: str = None,
                         issue_links: list = None,
                         execution_time: str = None):
        """
        Creates test execution result in current testcycle and testcase for specified status, executor and env
        :param status: testcase execution status. Auto set to Fail if any step is Fail.
        :param environment: env parameter. Must correspond to one in TM4J settings
        :param executed_by: name of person executed tests
        :param script_results: json with steps execution results
        :param comment: comment to testcase execution
        :param test_cycle_key: if provided overrides self.testrun['key']
        :param issue_links: test execution linked issues
        :param execution_time: test execution time
        """
        self.logger.info(f'Post results with params {locals()}')
        response = None
        key = test_cycle_key if test_cycle_key else self.testrun['key']
        if key is None:
            message = 'post_test_result: no testrun id found, call _post_new_testrun first'
            self.logger.debug(message)
            raise TM4JException(message)
        elif self.testcase['key'] is None:
            message = 'post_test_result: no testcase id found, call find_testcase("testcase", name)  first'
            self.logger.debug(message)
            raise TM4JException(message)
        else:
            self.testrun['key'] = key
            if script_results:
                script_results = validate_script_results_json(script_results)
                status = "Fail" if (list(filter(lambda step: step['status'] == "Fail", script_results))) else status
            else:
                script_results = TestScript.make_script_results(script=self.testcase['testScript'],
                                                                status=status)
            payload = dict({'status': status,
                            'environment': environment,
                            'comment': comment,
                            'executedBy': executed_by,
                            'scriptResults': script_results,
                            'issueLinks': issue_links,
                            'executionTime': execution_time})
            url = f'{self._baseurl}/testrun/{key}/testcase/{self.testcase["key"]}/testresult'
            try:
                response = self._do('post', url, strip_none_values(payload))
            except TM4JEnvironmentNotFound:
                new_environment = self._check_environment(env=environment)
                payload.update({'environment': new_environment})
                response = self._do('post', url, strip_none_values(payload))
            if response:
                self._testResultsId = response.get('id', None)
                self.logger.info(f'Test results posted successfully. Testcase:{self.testcase["key"]}, Results:{payload}')
            else:
                raise TM4JException(f'Cannot post test results.')

    def post_data_driven_test_results(self, test_case_execution: TestCaseExecution):
        """
        POst execution results from TestCaseExecution Datastructure. Can treat multiple
        DataRow executions for DD tests
        :param test_case_execution:
        :return:
        """
        testcase_key = self.find_testcase(key=test_case_execution.key,
                                          name=test_case_execution.name)
        execution_details = dict(status=test_case_execution.status,
                                 environment=test_case_execution.environment,
                                 executed_by=test_case_execution.executedBy,
                                 execution_time=str(test_case_execution.executionTime),
                                 test_cycle_key=test_case_execution.test_cycle_key)
        self.testrun['key'] = test_case_execution.test_cycle_key
        if test_case_execution.has_data_rows:
            testrun_item_id, testcase_last_test_result_id = self.get_testcase_run_id(testcase_key, **execution_details)
            self.put_update_script_status(testcase_last_test_result_id)
            test_case_execution.zip_with_id(self.get_datarow_ids(testrun_item_id))
            self.put_testscript_results(test_case_execution.jsonate())
            for item in test_case_execution.data_row_results:
                # testscript_steps_id_list[0] -- attach file to the first step in testscript
                self.attach_testcase_step_file(datarow_id=item.testscript_steps_id_list[0],
                                               file_path=item.log_file)
            self.logger.info(f'Posted {len(test_case_execution.data_row_results)} data row executions'
                        f'for testcase {testcase_key}')
        else:
            self.post_test_result(**execution_details)
            self.attach_testcase_result_file(file_path=test_case_execution[0].log_file)

    def get_testcase_run_id(self, key: str, **kwargs) -> tuple:
        """
        Function to get internal testrun item id and last execution id for testcase
        If no items found (testcase wasn't added into testrun) -- new test execution is created
        and function is recursively called
        :param key: testcase key
        :param kwargs: test execution details
        :return: testrunitem id, testcase lastTestResult id
        """
        self._get_tr_id()
        url = f'{self._serviceurl}/testrun/{self._tr_internal_id}/testrunitems?' \
            f'fields=id,index,issueCount,$lastTestResult'
        response = self._do('get', url, '')
        for item in response:
            if item['$lastTestResult']['testCase']['key'] == key:
                return item['id'], item['$lastTestResult']['id']
        self.post_test_result(**kwargs)
        return self.get_testcase_run_id(key=key)
        # raise TM4JObjectNotFound(f'Cannot find {key} run id in testrun {self._tr_internal_id}')

    def put_update_script_status(self, run_id):
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

    def get_datarow_ids(self, run_id: str) -> dict:
        """
        Function to get list of parameterset ids (datarow ids) - in order to post DD executions
        :param run_id: testcase run id.
        :return: dict of row id of the last (current) executions
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
            return result
        else:
            raise TM4JInvalidValue(f'No last execution found for run_id {run_id}')

    def put_testscript_results(self, script_results: str):
        """
        Function to post testcase rows execution results
        :param script_results: json (step execution id, result id, executed)
        :return:
        """
        url = f'{self._serviceurl}/testscriptresult/'
        self._do('put', url, payload=script_results)

    def attach_testrun_file(self, file_path: str):
        """
        Attach file to TestCycle execution. Must have value of *self.testrun['key']*
        -- create TestCycle beforehand.
        :param file_path:
        :return:
        """
        if self.testrun['key'] is not None:
            url = f'{self._baseurl}/testrun/{self.testrun["key"]}/attachments'
            with open(file_path, 'rb') as file:
                payload = {'file': file}
                self._do('post', url, payload, True)
            self.logger.debug(f'Attached file to testcycle {self.testrun["key"]}')
        else:
            raise TM4JException('attachTestResultFile: no testCycle id exists, call _post_new_testcycle first')

    def attach_testcase_result_file(self, file_path: str):
        """Attach file to TestCase execution. Must have value of *self._testResultsId*
-- call _post_new_testcycle beforehand."""
        if file_path:
            if self._testResultsId is not None:
                url = f'{self._baseurl}/testresult/{str(self._testResultsId)}/attachments'
                with open(file_path, 'rb') as file:
                    payload = {'file': file}
                    self._do('post', url, payload, True)
                self.logger.debug(f'Attached file to testcase {self.testcase["key"]}')
            else:
                raise TM4JException('attachTestResultFile: no testResult id exists, call postTestResults first')

    def attach_testcase_step_file(self, datarow_id: int, file_path: str):
        """
        Function to attach data row execution result
        :param datarow_id:
        :param file_path:
        :return:
        """
        if file_path:
            self.logger.debug(locals())
            url = f'{self._serviceurl}/testscriptresult/{datarow_id}/attachment'
            with open(file_path, 'rb') as file:
                payload = {'file': file}
                self._do('post', url, payload, True)
            self.logger.info(f'Attached file to row execution for {self.testcase["key"]}')

    def _get_all_project_testcases(self, max_results: int = 2000) -> list:
        url = f'{self._baseurl}/testcase/search?version=1.0&maxResults={max_results}&query=projectKey = "{self.project_key}"'
        response = self._do('get', url, '')
        self.logger.info(f'Got {len(response)} testcases')
        return response


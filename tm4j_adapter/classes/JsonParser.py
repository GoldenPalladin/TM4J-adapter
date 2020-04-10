import json
from classes.Parser import Parser
"""
Class to handle json-formated test execution results.
Format example:
    {"projectKey": "SIS",
    "testCaseKey": "SIS-T169",
    "status": "Pass",
    "comment": "pid:9893018",
    "executedBy": "dvallabhuni",
    "issueLinks": [],
    "scriptResults": [
        {"index": 0, "status": "Pass", "comment": "XX"},
        {"index": 1, "status": "Pass", "comment": "XX", "action":"XX"},
        {"index": 4, "status": "Pass", "comment": "XX", "action":"XX"}]}
"""


class JsonParser(Parser):
    def __init__(self, testcycle_name: str, config_path: str = None):
        super().__init__(config_path)
        self.testcycle_name = testcycle_name

    def _read_single_file(self, file_path: str):
        self.file = file_path
        with open(self.file) as f:
            self.file_contents = json.loads(f.read())

    def _parse_contents(self):
        parsed_contents = []
        if isinstance(self.file_contents, dict):
            parsed_contents.append(self.file_contents)
        elif isinstance(self.file_contents, list):
            parsed_contents.extend(self.file_contents)
        for result in parsed_contents:
            project_key = result['projectKey']
            testcase_key = result.get('testCaseKey', None)
            testcase_name = result.get('name', None)
            reporter = result['executedBy']
            comment = result['comment']
            status = self.match_execution_result(result['status'])
            issue_links = result.get('issueLinks', None)
            script_results = result.get('scriptResults', None)
            parse_result = project_key, testcase_key, testcase_name, status, comment, reporter, issue_links, script_results
            self.parse_results.append(parse_result)

    def _post_single_result(self, args: tuple):
        self.logger.debug(f'{locals()}')

        project_key, testcase_key, testcase_name, status, comment, reporter, issue_links, script_results = args[0]
        self.tm.find_testcase(name=testcase_name,
                              key=testcase_key,
                              folder=self.config['GENERAL']['tcFolder'])
        self.tm.post_test_result(status=status,
                                 environment=self.config['EXECUTION'].get('env'),
                                 executed_by=reporter,
                                 script_results=script_results,
                                 comment=comment,
                                 issue_links=issue_links)

    def do_export_results(self, args: tuple = None):
        self.tm.find_testcycle(self.testcycle_name, self.config['GENERAL']['trFolder'])
        super().do_export_results(args)
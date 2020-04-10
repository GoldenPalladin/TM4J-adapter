from classes.ThreadedParser import ThreadedParser
from classes.TM4J import TM4J
from libs.test_log_parser import parse_test_log
from libs.files import get_full_path
from xml.etree import ElementTree

"""
Class to handle execution report in JUnit .xml format
Format example:
    <testsuite name='PhotoUploaderUITests.CreatePatient' tests='5' failures='0'>
        <testcase classname='PhotoUploaderUITests.CreatePatient' name='testCreateJapanesePatient' time='29.580'/>
        <testcase classname='PhotoUploaderUITests.CreatePatient' name='testCreateNAPatient' time='32.169'/>
        <testcase classname='PhotoUploaderUITests.CreatePatient' name='testcreateRussianINVPatient' time='26.178'/>
        <testcase classname='PhotoUploaderUITests.CreatePatient' name='testINVClinicalConditionsPatientCreation' time='31.573'/>
        <testcase classname='PhotoUploaderUITests.CreatePatient' name='testTurkishPatient' time='28.200'/>
    </testsuite>
    <testsuite name='PhotoUploaderUITests.DemoAccountTest' tests='1' failures='1'>
        <testcase classname='PhotoUploaderUITests.DemoAccountTest' name='testDemoAccount'>
          <failure message='PhotoUploader crashed in @nonobjc UISegmentedControl.init()'>&lt;unknown&gt;:0</failure>
        </testcase>
    </testsuite>
"""


class JunitParser(ThreadedParser):
    def __init__(self, testcycle_name: str, config_path: str = None, testlogs_path: str = None):
        super().__init__(config_path)
        self.testcycle_name = testcycle_name
        # logs are provided as single file, attached to TestCycle, parsed and inserted as comment into test execution
        self.testlogs_path = get_full_path(testlogs_path, self.config['GENERAL']['useRelativePath'])
        self.test_logs = parse_test_log(self.testlogs_path) if testlogs_path else None

    def _read_single_file(self, file_path: str):
        self.file = file_path
        with open(self.file) as f:
            self.file_contents = ElementTree.parse(f)

    def _parse_contents(self):
        parsed_contents = []
        test_suites = self.file_contents.findall('testsuite')
        if not test_suites:
            raise ValueError("There are no test suites in parsed files")
        for test_suite in test_suites:
            for test_case in test_suite.findall('testcase'):
                parsed_contents.append(test_case)
        for result in parsed_contents:
            testcase_comment = ''
            testcase_name = result.get('name', None)
            testcase_execution_time = int(1000 * float(result.get('time', '0')))
            if self.test_logs:
                logs_details = self.test_logs.get(testcase_name, None)
                testcase_comment = f'<strong>Test logs data:</strong> {logs_details} <br>' if logs_details else ''
            failure_element = result.find('failure')
            if failure_element is not None:
                testcase_status = 'Fail'
                testcase_comment += f'<strong>Failure:</strong>{failure_element.get("message")}<br>{failure_element.text}'
            else:
                testcase_status = 'Pass'
            parse_result = testcase_name, testcase_status, testcase_comment, testcase_execution_time
            self.parse_results.append(parse_result)

    def _post_single_result(self, args: tuple):
        # need to instantiate separate tm instance to avoid concurrency issues in multithreading
        tm = TM4J(self.config_path)
        self.logger.debug(f'{locals()}')
        testcase_name, testcase_status, testcase_comment, testcase_execution_time = args
        tm.find_testcase(name=testcase_name,
                         folder=self.config['GENERAL']['tcFolder'])
        tm.post_test_result(status=testcase_status,
                            environment=self.config['EXECUTION']['env'],
                            executed_by=self.config['EXECUTION']['reporter'],
                            comment=testcase_comment,
                            execution_time=testcase_execution_time,
                            test_cycle_key=self.testcycle_key)

    def do_export_results(self, args: tuple = None):
        self.testcycle_key = self.tm.find_testcycle(self.testcycle_name, self.config['GENERAL']['trFolder'])
        if self.testlogs_path:
            self.tm.attach_testrun_file(self.testlogs_path)
        super().do_export_results(args)

    def manage_unposted_results(self, failed_posts: list):
        self.logger.error(f'Failed to post following results: {failed_posts}')


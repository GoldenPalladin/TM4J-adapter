from classes.ThreadedParser import ThreadedParser
from classes.TM4J import TM4J
from classes.DataStructures import TestsExecutionResults, TestCaseExecution
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from xml.dom.minidom import parseString
from libs.tags_parse_lib import clear_name
"""
Class to deal with rocs execution results provided in a single artifacts.zip file
.xml-report format:
    -<testsuite timestamp="2019-07-18T14:12:41.136257" time="2.038805" tests="1" skipped="0"
    name="tests.healthcheck.I have healthcheck link which i can follow and check current state"
    hostname="87c0e25a48cf"
    failures="0"
    errors="0">
        -<testcase time="2.038805" name="As admin I want to access Protocol ..."
        status="passed"
        classname="tests.healthcheck.I have healthcheck link which i can follow and check current state">
            -<system-out>
                -<![CDATA[
                @scenario.begin

                ...

                @scenario.end
                --------------------------------------------------------------------------------
                ]]>
            </system-out>
        </testcase>
    </testsuite>
"""


class RocsParser(ThreadedParser):
    def __init__(self, artifact_path: str, testcycle_name: str, config_path: str = None, testcycle_key: str = None):
        super().__init__(config_path)
        self.logger.info(f'Rocs parser with args {locals()}')
        self.testcycle_name = testcycle_name
        self.testcycle_key = testcycle_key
        self.artifact_path = artifact_path
        self.parse_results = TestsExecutionResults(status_codes=self.tm.get_project_testresult_status_codes())

    def read_files(self, files=None):
        """
        override method to deal with one single file
        """
        self.logger.info(f'Parsing {self.artifact_path}')
        self.parse_results.clear()
        files_counter = 0
        with ZipFile(self.artifact_path, 'r') as artifacts_zip:
            tempdir = tempfile.mkdtemp()
            for filename in artifacts_zip.namelist():
                if ".xml" in filename:
                    files_counter += 1
                    xml_file = filename
                    logfile_name = "split_" + filename.split(".")[-2] + "_feature.log"
                    with artifacts_zip.open(filename) as report:
                        dom = parseString(report.read())
                    testcase_key, testcase_name, testcase_example_row = \
                        self.get_splitted_data(name=dom.getElementsByTagName("testcase")[0].attributes['name'].value,
                                               delimiter=self.config['GENERAL']['testCaseKeyDelimiter'])
                    testcase_status = self.match_execution_result(dom.getElementsByTagName("testcase")[0]
                                                                  .attributes['status'].value)
                    testcase_execution_time = int(1000 * float(dom.getElementsByTagName("testcase")[0]
                                                               .attributes['time'].value))
                    logfile = artifacts_zip.extract(logfile_name, tempdir)
                    tce = self.parse_results.add_result(*(testcase_key, testcase_name, testcase_status, logfile,
                                                          xml_file, testcase_execution_time, testcase_example_row))
                    tce.update(environment=self.config['EXECUTION']['env'],
                               executedBy=self.config['EXECUTION']['reporter'])
        self.export_results['Files read'] = files_counter
        self.export_results.update({'Testcases': len(self.parse_results)})
        self.logger.info(f'Parsed {files_counter} files with test results, {len(self.parse_results)} testcases')

    def _post_single_result(self, tce: TestCaseExecution):
        # need to instantiate separate tm instance to avoid concurrency issues in multithreading
        tm = TM4J(self.config_path)
        self.logger.debug(f'{locals()}')
        tm.post_data_driven_test_results(tce)

    def do_export_results(self, args: tuple = None):
        if not self.testcycle_key:
            self.testcycle_key = self.tm.find_testcycle(name=self.testcycle_name,
                                                        folder=self.config['GENERAL']['trFolder'],
                                                        linked_issues=self.config['EXECUTION']['jiraTaskList'])
        self.parse_results.set_testrun_key(self.testcycle_key)
        super().do_export_results(args)
        self.logger.info(f'\n\nRocs test execution summary:\n'
                         f'{"-" * 25}\n'
                         f'Created testcycle {self.testcycle_key}: {self.testcycle_name}\n'
                         f'Tests executed in Rocs: {self.export_results["Files read"]}\n'
                         f'Testcases to be posted in testcycle: {self.export_results["Testcases"]}\n'
                         f'Tests exported successfully: {self.export_results["Exported"]}\n'
                         f'Tests failed to export: {self.export_results["Failed"]}')

    def manage_unposted_results(self, failed_posts: TestsExecutionResults):
        """
        Function creates archive with unsuccessfully posted files passed in lists
        :param failed_posts: unsuccessfully posted results
        :return:
        """
        self.logger.info(f'Extracting unposted test results')
        failed_artifacts_path = f'{self.artifact_path[:-4]}_not_posted.zip'
        with ZipFile(self.artifact_path, 'r') as artifacts:
            with ZipFile(failed_artifacts_path, 'w', compression=ZIP_DEFLATED) as failed_artifacts:
                try:
                    for failed_post in failed_posts:
                        for files in failed_post.get_files_list():
                            xml_file = files[0]
                            failed_artifacts.writestr(xml_file, artifacts.read(xml_file))
                            logfile_name = "split_" + xml_file.split(".")[-2] + "_feature.log"
                            failed_artifacts.writestr(logfile_name, artifacts.read(logfile_name))
                except Exception as e:
                    print(e)
        self.logger.info(f'Results extracted to {failed_artifacts_path}')

    @staticmethod
    def get_splitted_data(name: str, delimiter: str) -> tuple:
        from re import search
        from libs.tags_parse_lib import split_testcase_name_key
        row_num = 0
        # trim rocs splitting names formatting
        if '@' in name:
            testcase_name = (name.split('@')[0])[:-3]
            match = search(r'(?<=.)\d+', name.split('@')[1])
            row_num = int(match.group(0)) if match else row_num
        else:
            testcase_name = name
        testcase_key, testcase_name = split_testcase_name_key(testcase_name, delimiter)
        return testcase_key, clear_name(testcase_name), row_num


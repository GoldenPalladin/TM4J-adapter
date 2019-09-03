"""
Library implements parsing junit reports into TM4J testruns and testresults
"""

import xmltodict
import logging
import logging.config
import json
import argparse
from tmconnect import TM4J, TestScript, TM4JObjectNotFound
from files import get_list_of_files
from os import path
from test_log_parser import parse_test_log
from tm_log import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('junitParser')


def parse_junit_file(tm, file, testcycle_name, export_results, logs_path=None):
    """reads junit file and creates testcases with steps and step execution results"""
    logger.info(f'parse_json_file: {locals()}')
    with open(file) as f:
        junit_json = json.loads(json.dumps(xmltodict.parse(f.read())))
        test_run = junit_json.get('testsuites', None)
        testcases = list()
        if test_run:
            # assert isinstance(test_run['testsuite'], list)
            testcases.extend(test_run['testsuite'])
        else:  # if there is a single test executed, no <testsuites> tag is created
            testcases.append(junit_json.get('testsuite', None))  # get suite name as testcase name
        tm.find_testrun(testcycle_name, tm.config['GENERAL']['trFolder'])
        if logs_path:
            test_logs_file_path = path.join(path.abspath(path.dirname(__file__)), logs_path)
            test_logs = parse_test_log(test_logs_file_path)
            tm.attach_testrun_file(test_logs_file_path)
        else:
            test_logs = None
        if testcases[0] is None:
            raise ValueError(f'No testsuite found in xml-file')
        for test in testcases:
            tm.find_testcase(test['@name'], None, tm.config['GENERAL']['tcFolder'])
            ts = TestScript()
            if 'testScript' in tm.testcase:
                ts.script = tm.testcase['testScript']
            steps = test['testcase']
            if isinstance(steps, list):
                for step in steps:
                    parse_step(ts, step, test_logs)
            else:
                parse_step(ts, steps, test_logs)
            tm.testcase['testScript'] = ts.script
            updated_values = tm.testcase
            tm.update_testcase(updated_values)
            try:
                tm.post_test_result('Pass', tm.config['JUNIT']['env'], tm.config['JUNIT']['reporter'], ts.results)
                export_results['Exported'] += 1
            except Exception as e:
                export_results['Failed'] += 1
                logger.error(f"parse_json_file: Error adding results for testcase {tm.testcase['name']}: {e}")
    return export_results


def parse_step(ts, step, test_logs=None):
    """ function add step results from step to ts
    :param ts: TestScript object to append step results
    :param step: junit parsed test steps dictionary
    :param test_logs: parsed logs dictionary"""
    comment = ''
    if test_logs:
        step_name = step['@name']
        comment = f'<strong>Test logs data:</strong> {", ".join(test_logs.get(step_name, ""))} <br>'
    if 'failure' in step:
        status = 'Fail'
        comment += f'<strong>Failure:</strong>{step["failure"]["@message"]}<br>{step["failure"]["#text"]}'
    else:
        status = 'Pass'
    logger.debug(f'parse step: {step["@name"]}, {status}, {comment}')
    ts.set_step_results(step['@name'], status, comment)


def main():
    export_results = {'junit files': 0, 'Exported': 0, 'Failed': 0}
    tm = TM4J()
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--tc_name", help="Test cycle name")
    parser.add_argument("-f", "--j_file", help="Path to junit.xml")
    parser.add_argument("-o", "--j_folder", help="Path to folder with junit results")
    parser.add_argument("-l", "--logs", help="Path to test execution logs")
    args = parser.parse_args()
    junit_file = args.j_file if args.j_file else tm.config['JUNIT']['junitFile']
    junit_folder = args.j_folder if args.j_folder else tm.config['JUNIT']['junitFolder']
    parse_folder = 'True' if args.j_folder else tm.config['JUNIT']['parseFolder']
    testcycle_name = args.tc_name if args.tc_name else tm.config['JUNIT']['testcycleName']
    logs_path = args.logs if args.logs else \
        (tm.config['JUNIT']['pathToLogs'] if tm.config['JUNIT']['pathToLogs'] != '' else None)

    if parse_folder == 'True':
        files_list = get_list_of_files(
            path.join(path.abspath(path.dirname(__file__)), junit_folder)
            , '.xml')
        export_results['junit files'] = len(files_list)
        for file in files_list:
            logger.debug(f'parsing junit file: {file}')
            export_results = parse_junit_file(tm, file, testcycle_name, export_results, logs_path)
    else:
        file = path.join(path.abspath(path.dirname(__file__)),
                         junit_file)
        export_results = parse_junit_file(tm, file, testcycle_name, export_results, logs_path)
        export_results['junit files'] = 1

    logger.info(f'TC export results: {export_results}')


if __name__ == '__main__':
    main()

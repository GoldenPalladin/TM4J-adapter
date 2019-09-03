"""
Library implements parsing json-based reports into TM4J testruns and testresults
"""

import logging
import logging.config
import json
import argparse
from tmconnect import TM4J
from files import get_list_of_files
from os import path
from tm_log import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('jsonParser')


def parse_json_file(tm, file, testcycle_name, export_results):
    """reads junit file and creates testcases with steps and step execution results"""
    logger.info(f'parse_json_file: {locals()}')
    results = []
    with open(file) as f:
        content = json.loads(f.read())
        if isinstance(content, dict):
            results.append(content)
        elif isinstance(content, list):
            results.extend(content)
        for test in results:
            tm.project_key = test['projectKey']
            tm.find_testrun(testcycle_name, tm.config['GENERAL']['trFolder'])
            try:
                tc_name = test['name']
            except KeyError:
                tc_name = None
            tm.find_testcase(tc_name, test['testCaseKey'], tm.config['GENERAL']['tcFolder'])
            ts = test['scriptResults']
            reporter = test['executedBy']
            comment = test['comment']
            try:
                tm.post_test_result('Pass', tm.config['JSON']['env'], reporter, ts, comment)
                export_results['Exported'] += 1
            except Exception as e:
                export_results['Failed'] += 1
                logger.error(f"parse_json_file: Error adding results for testcase {tm.testcase['name']}: {e}")
    return export_results


def main():
    export_results = {'json files': 0, 'Exported': 0, 'Failed': 0}
    tm = TM4J()
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--tc_name", help="Test cycle name")
    parser.add_argument("-f", "--j_file", help="Path to json file")
    parser.add_argument("-o", "--j_folder", help="Path to folder with json files")
    args = parser.parse_args()
    junit_file = args.j_file if args.j_file else tm.config['JSON']['jsonFile']
    junit_folder = args.j_folder if args.j_folder else tm.config['JSON']['jsonFolder']
    parse_folder = 'True' if args.j_folder else tm.config['JSON']['parseFolder']
    testcycle_name = args.tc_name if args.tc_name else tm.config['JSON']['testcycleName']

    if parse_folder == 'True':
        files_list = get_list_of_files(
            path.join(path.abspath(path.dirname(__file__)), junit_folder)
            , '.json')
        export_results['json files'] = len(files_list)
        for file in files_list:
            logger.debug(f'parsing json file: {file}')
            export_results = parse_json_file(tm, file, testcycle_name, export_results)
    else:
        file = path.join(path.abspath(path.dirname(__file__)),
                         junit_file)
        export_results = parse_json_file(tm, file, testcycle_name, export_results)
        export_results['json files'] = 1

    logger.info(f'TC export results: {export_results}')


if __name__ == '__main__':
    main()

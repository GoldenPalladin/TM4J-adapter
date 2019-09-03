"""
Library implements parsing BDD feature files into TM4J testcases
"""

import re
import logging.config
from os import path
from tmconnect import TM4J, TestScript, TestParameters
from behave import parser as pr
from files import get_list_of_files
from tm_log import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('bddParser')


def parse_feature_file(file_path: str, configs: dict) -> list:
    """function returns list of json testcases"""
    result = []
    tp = TestParameters()
    feature = pr.parse_file(file_path)
    feature_link = f'{configs["BDD"]["repoLink"]}/{path.relpath(file_path, configs["BDD"]["featuresFolder"])}'\
        .replace('\\', '/')
    if len(feature.scenarios) == 0:
        raise LookupError('no scenarios found in .feature file')
    for scenario in feature.scenarios:
        parsed_tags = parse_scenario_tags(scenario.tags)
        description_list = scenario.description
        description_list.insert(0, scenario.name)
        name = "".join(description_list)
        testcase = {
            "projectKey": configs['GENERAL']['tm4jProjectKey'],
            "name": name,
            "precondition": "The precondition.",
            "objective": name,
            "folder": f"/{configs['GENERAL']['tcFolder']}",
            "status": "Approved",
            "priority": parsed_tags['priority'],
            "labels": parsed_tags['tags'] + feature.tags,
            "link": feature_link
        }
        if configs['BDD']['parseJiraTags'] == 'True':
            testcase.update({"issueLinks": [parsed_tags['jira']]})
        testcase.update({"testScript": parse_steps_to_script(scenario.steps)})
        if hasattr(scenario, 'examples') and hasattr(scenario.examples[0], 'table'):
            table = scenario.examples[0].table
            tp.set_variables(table.headings)
            for row in table.rows:
                tp.append_values(row.headings, row.cells)
            logger.debug(f'TP: {tp.parameters}')
            testcase.update({'parameters': tp.parameters})
        result.append(testcase)
        return result


def parse_steps_to_script(steps):
    """function parses gherkin steps into description-expected test script"""
    ts = TestScript()
    test_step = {'description': '', 'data': '', 'expected': ''}
    previous_step = None
    for step in steps:
        test_data = repl_braces(step.text) if step.text else ''
        if step.keyword in ('Given', 'When'):
            if previous_step == 'expected':
                ts.append_step(test_step['description'], test_step['data'], test_step['expected'])
                test_step = {'description': '', 'data': '', 'expected': ''}
            previous_step = 'description'
            test_step[previous_step] += step.keyword + " " + repl_braces(step.name) + '\r\n'
            test_step['data'] += test_data
        elif step.keyword == 'Then':
            previous_step = 'expected'
            test_step[previous_step] += step.keyword + " " + repl_braces(step.name) + '\r\n'
            test_step['data'] += test_data
        elif step.keyword == 'And':
            test_step[previous_step] += step.keyword + " " + repl_braces(step.name) + '\r\n'
            test_step['data'] += test_data
    ts.append_step(test_step['description'], test_step['data'], test_step['expected'])
    return ts.script


def repl_braces(text: str) -> str:
    """Function proceeds parameters bracketing"""
    return text.replace('<{', '||').replace('}>', '||').replace('{', '|').replace('}', '|')\
        .replace('<', '{').replace('>', '}')


def is_jira_issue(tag: str) -> bool:
    return bool(re.search(r'(?<!([^\s]))([A-Z,1-9]{1,10}-[1-9][0-9]{0,6})(?=(\s|$))', tag))


def is_priority(tag: str) -> bool:
    return bool(re.search(r'P[0-3]', tag))


def parse_scenario_tags(tags: list) -> dict:
    """tags split into jira, priority or tags list"""
    PRIORITY_MAP = {'P2': 'High', 'P1': 'Normal', 'P0': 'Low'}
    try:
        jira_tag = list(filter(lambda tag: is_jira_issue(tag), tags))[0]
    except IndexError:
        jira_tag = None
    priority_tag = PRIORITY_MAP[list(filter(lambda tag: is_priority(tag), tags))[0]]
    other_tags = list(filter(lambda tag: (not is_jira_issue(tag)) and (not is_priority(tag)), tags))
    result = {"jira": jira_tag,
              "priority": priority_tag,
              "tags": other_tags}
    logger.debug(f'parse_scenario_tags: {result}')
    return result


def post_testcases(tm: TM4J, testcases: list, export_results: dict = None) -> (list, dict):
    """function creates testcases in TM4J from parsed json

    :param tm: TM4J object
    :param testcases: list of parsed in parse_feature_file testcases. List of specific json format
    :param export_results: success/failure exports counter
    :return: list of created testcase keys"""
    posted_tc_keys = []
    tc_failures = 0
    for testcase in testcases:
        try:
            tm.find_testcase(testcase['name'])
            feature_file_link = testcase.pop('link')
            tm.update_testcase(testcase)
            tm.add_weblink(feature_file_link, feature_file_link)
            posted_tc_keys.append(tm.testcase['key'])
            export_results['Testcases imported'] += 1
        except Exception as e:
            logger.exception(f'post_testcases error: {testcase}: {e}')
            tc_failures += 1
    logger.info(f'Successfully imported {str(len(testcases) - tc_failures)} testcases. '
                f'Failed {tc_failures} testcases')
    return posted_tc_keys, export_results


def post_testacases_from_feature_file(tm: TM4J, file: str, export_results: dict) -> dict:
    """
    function post tescases from passed feature file and returns results dict
    :param tm: TM4J instance
    :param file: path to feature file
    :param export_results: export results dict
    :return: updated export results dict
    """
    try:
        logger.debug(f'parsing feature file: {file}')
        test_cases = parse_feature_file(file, tm.config)
        export_results['Proceeded'] += 1
        export_results = post_testcases(tm, test_cases, export_results)[1]
    except Exception as e:
        logger.error(f'Parsing file {file}:\n {e}')
        export_results['Failed'] += 1
    return export_results


def main():
    export_results = {'Feature files found': 0, 'Proceeded': 0, 'Failed': 0, 'Testcases imported': 0}
    tm = TM4J()
    parse_folder = path.join(path.abspath(path.dirname(__file__)), tm.config['BDD']['featuresFolder'])
    if tm.config['BDD']['parseFolder'] == 'True':
        files_list = get_list_of_files(parse_folder, '.feature')
        export_results['Feature files found'] = len(files_list)
        for file in files_list:
            post_testacases_from_feature_file(tm, file, export_results)
    else:
        file = path.join(parse_folder, tm.config['BDD']['featuresFile'])
        export_results['Feature files found'] = 1
        post_testacases_from_feature_file(tm, file, export_results)
    logger.info(f'TC export results: {export_results}')


if __name__ == '__main__':
    main()

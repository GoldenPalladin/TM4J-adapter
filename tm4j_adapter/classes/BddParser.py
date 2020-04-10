from classes.Parser import Parser
from classes.TestScript import TestScript
from classes.TestParameters import TestParameters
from libs.tags_parse_lib import parse_scenario_tags, split_testcase_name_key
from behave import parser as pr
from libs.files import FilesHandler
from libs.update_tests_with_keys import update_feature_file_with_keys
"""
Class to deal with Behave .feature files
Format example:
    Feature: We should be able to get user filters
      @CST-1360 @P0 @get_filters_action_availability
      Scenario Outline: CST-T104_As a doctor I want to have "filters" action available for me
        Given I access "gallery" api as "<user>"
        When I am at "<home>" resource
        Then It has action "filters"
        And ---- newline---
        Examples: users
          | user         | home       |
          | default_user | DoctorHome |
          | go_doctor    | DoctorHome |
"""


class BddParser(Parser):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)

    def _read_single_file(self, file_path: str):
        fh = FilesHandler(self.config, file_path)
        feature = pr.parse_file(file_path)
        feature_folder_name, feature_link = fh.get_bdd_file_paths()
        if len(feature.scenarios) == 0:
            raise LookupError('no scenarios found in .feature file')
        precondition = feature.background.name if feature.background else ''
        objective = feature.name
        for scenario in feature.scenarios:
            if feature.tags:
                scenario.tags.extend(feature.tags)
            parsed_scenario = scenario, precondition, objective, file_path, feature_folder_name, feature_link
            self.file_contents.append(parsed_scenario)

    def _parse_contents(self):

        def has_obsolete_tags(tags: list) -> bool:
            tags_to_exclude = (self.config["BDD"]["tagsToExclude"]).strip().split(',')
            tags_to_exclude = [] if tags_to_exclude[0] == '' else tags_to_exclude
            for parsed_tag in tags:
                if parsed_tag in tags_to_exclude:
                    self.logger.info(f'Scenario {name} is tagged as obsolete and will be skipped!')
                    return True

        for parsed_scenario in self.file_contents:
            scenario, precondition, objective, feature_file_path, feature_folder_name, feature_link = parsed_scenario
            parsed_tags = dict()
            name = f'{scenario.name}{scenario.description}'.replace('[]', '')
            # starting from tags to skip scenarios tagged as obsolete or deprecated
            if scenario.tags:
                parsed_tags = parse_scenario_tags(scenario.tags)
                if has_obsolete_tags(parsed_tags['labels']):
                    continue
                if self.config['BDD']['parseJiraTags'] != 'True':
                    parsed_tags.pop('issueLinks', None)
            n_key, n_name = split_testcase_name_key(name, self.config['GENERAL']['testCaseKeyDelimiter'])
            feature_folder_name = '...' if (feature_folder_name == '') else feature_folder_name
            sub_folder = f"/{feature_folder_name}" if (self.config['BDD']['copyFolderStructure'] == 'True') \
                else ''
            testcase = {
                "projectKey": self.config['GENERAL']['tm4jProjectKey'],
                "key": n_key,
                "name": n_name,
                "precondition": precondition,
                "objective": objective,
                "folder": f"{self.config['GENERAL']['tcFolder']}{sub_folder}",
                "status": "Approved",
                "link": feature_link,
                "feature_file_path": feature_file_path
            }
            testcase.update(parsed_tags)
            testcase.update({"testScript": parse_steps_to_script(scenario.steps)})
            if hasattr(scenario, 'examples') and hasattr(scenario.examples[0], 'table'):
                tp = TestParameters()
                table = scenario.examples[0].table
                tp.set_variables(table.headings)
                for row in table.rows:
                    tp.append_values(row.headings, row.cells)
                testcase.update({'parameters': tp.parameters})
            self.parse_results.append(testcase)
            self.export_results['Results found'] += 1

    def _post_single_result(self, args: tuple):
        self.logger.debug(f' {locals()}')
        testcase, = args
        feature_file_link = testcase.pop('link')
        feature_file_path = testcase.pop('feature_file_path')
        try:
            key = self.tm.find_testcase(name=testcase['name'],
                                        key=testcase['key'],
                                        folder=testcase['folder'],
                                        test_source_file_path=feature_file_path,
                                        autocreate=True)
            self.tm.update_testcase(testcase)
            self.tm.add_testcase_weblink(description=feature_file_link, link_url=feature_file_link)
            if self.config['BDD']['updateFeatureFileOnExport'] == 'True':
                update_feature_file_with_keys(key=key,
                                              name=testcase['name'],
                                              feature_file_path=feature_file_path)
            # get back feature_file_path for unit testing since Python pop update
            # self.testcase object
            testcase.update({'feature_file_path': feature_file_path,
                             'key': key})
        except Exception as e:
            text = e.response.content if hasattr(e, 'response') else e
            self.logger.error(f'post_testcases error: {text}. Feature file: {feature_file_link}, testcase: {testcase}')
            raise e


def parse_steps_to_script(steps):
    """function parses gherkin steps into description-expected test script"""
    ts = TestScript()
    test_step = {'description': '', 'data': '', 'expected': ''}
    previous_step = None
    for step in steps:
        test_data = f'<br>{repl_braces(step.text)}' if step.text else ''
        if step.keyword.capitalize() in ('Given', 'When'):
            if previous_step == 'expected':
                ts.append_step(test_step['description'], test_step['data'], test_step['expected'])
                test_step = {'description': '', 'data': '', 'expected': ''}
            previous_step = 'description'
            test_step[previous_step] += f'{step.keyword} {repl_braces(step.name)}{test_data}<br>'
        elif step.keyword.capitalize() == 'Then':
            previous_step = 'expected'
            test_step[previous_step] += f'{step.keyword} {repl_braces(step.name)}{test_data}<br>'
        elif step.keyword.capitalize() == 'And':
            previous_step = 'description' if not previous_step else previous_step
            # in case if we start with no Given step
            # and no expected step is described
            test_step[previous_step] += f'{step.keyword} {repl_braces(step.name)}{test_data}<br>'
    ts.append_step(test_step['description'], test_step['data'], test_step['expected'])
    return ts.script


def repl_braces(text: str) -> str:
    """Function proceeds parameters bracketing"""
    return text.replace('<{', '||').replace('}>', '||').replace('{', '|').replace('}', '|') \
        .replace('<', '{').replace('>', '}').replace('\r\n', '<br>  ')

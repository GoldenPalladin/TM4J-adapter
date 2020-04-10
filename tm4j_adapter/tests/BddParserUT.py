import shutil
import unittest
from unittest.mock import patch
from os import path, walk
from bdd_parser import get_list_of_feature_files_to_proceed
from classes.BddParser import BddParser
from libs.config import read_config
from libs.files import get_full_path
from libs.tags_parse_lib import split_testcase_name_key
from tests.config import bdd_config
from behave import parser as pr
from tests.TestData.MockedTm4j import mocked_tm4j
from libs.update_tests_with_keys import update_feature_file_with_keys
from filecmp import cmp


class BddParse(unittest.TestCase):
    """
    - check steps
    - check data
    - send API call and check json
    """
    @classmethod
    def setUpClass(cls) -> None:
        # copy blank feature files
        source = get_full_path(base_path=bdd_config['featuresSrc'],
                               use_relative_path=True)
        destination = get_full_path(base_path=bdd_config['featuresDst'],
                                    use_relative_path=True)
        try:
            shutil.rmtree(destination)
        except Exception as e:
            pass
        shutil.copytree(source, destination)
        cls.parseconfig = read_config(bdd_config['configPath'])
        cls.files_list = get_list_of_feature_files_to_proceed(cls.parseconfig)
        cls.bdd_parser = BddParser(bdd_config['configPath'])
        cls.bdd_parser.read_files(cls.files_list)
        cls.allParseResults = list()
        cls.destination = destination

    @classmethod
    def tearDownClass(cls) -> None:
        destination = get_full_path(base_path=bdd_config['featuresDst'],
                                    use_relative_path=True)
        shutil.rmtree(destination)


class ParsingChecks(BddParse):
    def test_check_testcases_amount(self):
        self.assertEqual(len(self.bdd_parser.file_contents), 10)

    def test_parse_folder_structure(self):
        parsed_folders_list = [result['folder'] for result in self.bdd_parser.parse_results]
        features_folder_root = path.join(path.abspath(path.dirname(path.dirname(__file__))),
                                         path.join(self.parseconfig["BDD"]["localRepoRoot"],
                                                   self.parseconfig["BDD"]["featuresFolderInLocalRepository"]))
        feature_files_list = [path.join(dp, f) for dp, dn, fn in walk(features_folder_root) for f in fn]
        print(feature_files_list)
        feature_folders_list = list(map(lambda x: f'{self.parseconfig["GENERAL"]["tcFolder"]}/{x}'.replace('.', '...').replace(' ', '_'),
                                        map(lambda x: path.relpath(x, features_folder_root),
                                            map(lambda x: path.dirname(x),
                                                filter(lambda x: path.splitext(x)[1] == '.feature',
                                                       feature_files_list)))))
        self.assertSetEqual(set(parsed_folders_list), set(feature_folders_list))

    def test_parsed_tags(self):
        parsed_tags_list = sorted([sorted(result['labels']) for result in self.bdd_parser.parse_results])
        tags_list = sorted(list(map(lambda x: sorted(x),
                                [['gallery_api', 'get_gallery_filters', 'get_filters_action_availability'],
                                ['gallery_api', 'get_gallery_filters', 'anonimized_filters_info'],
                                ['gallery_api', 'get_gallery_filters', 'non_anonimized_filters_info'],
                                ['gallery_api', 'pr', 'smoke', 'galley_api_healthcheck'],
                                ['gallery_api', 'search_gallery_cases', 'search_cases_action_availability'],
                                ['gallery_api', 'search_gallery_cases', 'search_cases_action_availability'],
                                ['gallery_api', 'search_gallery_cases', 'search_not_incorrect_param'],
                                ['gallery_api', 'search_gallery_cases', 'search_not_anonym_cases_by_default'],
                                ['gallery_api', 'search_gallery_cases', 'check_gallery_case_collections_type'],
                                ['gallery_api', 'search_gallery_cases', 'check_anonymized_cases']])))
        self.assertListEqual(parsed_tags_list, tags_list)


class PostingChecks(BddParse):
    def setUp(self):
        self.allParseResults = self.bdd_parser.parse_results
        # leave testcase with the longest folder name
        self.bdd_parser.parse_results = sorted(self.bdd_parser.parse_results, key=lambda x: x['folder'])[-1:]

    def test_post_testcase_to_check_parsed_folder(self):
        self.bdd_parser.do_export_results()
        self.assertEqual(self.bdd_parser.export_results['Failed'], 0)
        key = self.bdd_parser.parse_results[0]['key']
        self.bdd_parser.tm._delete_testcase(key)
        self.assertIsNotNone(key)

    def tearDown(self) -> None:
        self.bdd_parser.parse_results = self.allParseResults


class FeatureFileUpdate(BddParse):

    def setUp(self) -> None:
        self.allParseResults = self.bdd_parser.parse_results
        # take just one result to check
        self.bdd_parser.parse_results = self.bdd_parser.parse_results[:1]

    def test_update_tc_having_key(self):
        self.before_feature = path.join(self.destination, 'test_update_tc_having_key_before.feature')
        self.after_feature = path.join(self.destination, 'test_update_tc_having_key_after.feature')
        kwargs = {'key': 'CST-T137',
                  'name': 'As an admin I want to have "search-cases" action NOT available for me',
                  'feature_file_path': self.before_feature}
        update_feature_file_with_keys(**kwargs)
        self.assertTrue(cmp(self.before_feature, self.after_feature))

    def test_update_new_tc(self):
        self.before_feature = path.join(self.destination, 'test_update_new_tc_before.feature')
        self.after_feature = path.join(self.destination, 'test_update_new_tc_after.feature')
        kwargs = {'key': 'CST-T135',
                  'name': 'As a doctor I want to have "search-cases" action available for me',
                  'feature_file_path': self.before_feature}
        update_feature_file_with_keys(**kwargs)
        self.assertTrue(cmp(self.before_feature, self.after_feature))

    def test_every_feature_test_updated_with_keys(self):
        expected_export_results = {'Files read': 3, 'Results found': 1, 'Exported': 1, 'Failed': 0}
        with patch('classes.tmconnect.TM4J', new=mocked_tm4j) as patched_tm4j:
            self.bdd_parser.tm = patched_tm4j
            self.bdd_parser.do_export_results()
            self.assertDictEqual(self.bdd_parser.export_results, expected_export_results)
        posted_testcase = self.bdd_parser.parse_results[0]
        feature = pr.parse_file(posted_testcase['feature_file_path'])
        feature_tests = dict()
        posted_test = {'CST-T1': posted_testcase['name']}
        for scenario in feature:
            scenario_name = f'{str(scenario.name)}{str(scenario.description)}'.replace('[]', '')
            n_key, n_name = split_testcase_name_key(scenario_name, self.parseconfig['GENERAL']['testCaseKeyDelimiter'])
            feature_tests.update({n_key: n_name})
        self.assertTrue(feature_tests.items() >= posted_test.items())

    def tearDown(self) -> None:
        self.bdd_parser.parse_results = self.allParseResults


if __name__ == '__main__':
    unittest.main()


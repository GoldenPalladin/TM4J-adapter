import unittest
from os import remove
from unittest.mock import patch, Mock, call
from classes.RocsParser import RocsParser
from libs.config import read_config
from libs.files import get_full_path
from libs.bamboo import get_build_artifact
from tests.config import rocs_config
from os.path import exists
from tests.TestData.MockedTm4j import mocked_tm4j


class RocsParse(unittest.TestCase):
    """
    - exceptioned results are retried
    - unposted results are saved
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.parseconfig = read_config(rocs_config['configPath'])
        cls.artifact_path = get_full_path(cls.parseconfig['ROCS']['pathToArtifact'], True)
        cls.rocs_parser = RocsParser(artifact_path=cls.artifact_path,
                                     config_path=rocs_config['configPath'],
                                     testcycle_name=cls.parseconfig['EXECUTION']['testcycleName'])
        cls.rocs_parser.tm = mocked_tm4j
        cls.allParseResults = list()
        cls.current_result = None
        cls.rocs_parser.read_files()


class GetBambooArtifact(RocsParse):

    def test_get_bamboo_artifact(self):
        build_url = self.parseconfig['ROCS']['bambooBuildLink']
        artifact_path = get_full_path(rocs_config['pathForBambooArtifact'], True)
        get_build_artifact(build_url, artifact_path)
        self.assertTrue(exists(artifact_path))
        remove(artifact_path)


class TestFilesParsing(RocsParse):

    def test_executions_amount(self):
        print(self.rocs_parser.parse_results.status_codes)
        test_results = {'Pass': 0, 'Fail': 0, 'Total': 0}
        expected_test_results = {'Pass': 121, 'Fail': 8, 'Total': 129}
        for result in self.rocs_parser.parse_results:
            print(result)
            for execution in result.data_row_results:
                test_results['Total'] += 1
                if execution.testResultStatusId == 929:
                    test_results['Pass'] += 1
                elif execution.testResultStatusId == 930:
                    test_results['Fail'] += 1
        self.assertDictEqual(test_results, expected_test_results)


class TestResultsMockedPost(RocsParse):

    def setUp(self):
        self.allParseResults = self.rocs_parser.parse_results
        self.rocs_parser.parse_results = self.rocs_parser.parse_results[:1]
        self.current_result = self.rocs_parser.parse_results[0]

    @patch('classes.ThreadedParser.ThreadedParser.do_export_results',
           new=Mock())
    def test_testcycle_creation(self):
        testrun = call(self.parseconfig['EXECUTION']['testcycleName'],
                       self.parseconfig['GENERAL']['trFolder'])
        self.rocs_parser.do_export_results()
        self.assertEqual(mocked_tm4j.find_testcycle.call_args, testrun)
        self.assertEqual(self.rocs_parser.testcycle_key, 'CST-R1')

    def test_results_posting(self):
        self.rocs_parser.testcycle_key = 'CST-R1'
        with patch('classes.RocsParser.TM4J', new=mocked_tm4j) as patched_tm:
            self.rocs_parser._post_single_result(self.current_result)
            tm_calls = patched_tm.mock_calls
            self.assertEqual(tm_calls[1][1][0], self.current_result)

    def test_unposted_save(self):
        self.rocs_parser.manage_unposted_results(self.allParseResults)
        failed_artifacts_path = f'{self.rocs_parser.artifact_path[:-4]}_not_posted.zip'
        self.assertTrue(exists(failed_artifacts_path))
        self.rocs_parser.artifact_path = failed_artifacts_path
        self.rocs_parser.read_files()
        self.assertListEqual(self.allParseResults, self.rocs_parser.parse_results)


class TestResultsLivePost(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.parseconfig = read_config(rocs_config['configPath'])
        cls.artifact_path = get_full_path(cls.parseconfig['ROCS']['pathToArtifact'], True)
        cls.rocs_parser = RocsParser(artifact_path=cls.artifact_path,
                                     config_path=rocs_config['configPath'],
                                     testcycle_name=cls.parseconfig['EXECUTION']['testcycleName'])

    def test_results_posting(self):
        self.rocs_parser.read_files()
        self.rocs_parser.do_export_results()


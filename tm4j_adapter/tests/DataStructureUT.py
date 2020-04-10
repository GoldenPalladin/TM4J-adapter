import unittest
from unittest.mock import patch, Mock
import json
from classes.DataStructures import TestCaseExecution, DataRowResult, TestsExecutionResults
from tests.TestData.tmconnect.prefilled_tm4j_items import cst_t1973_tce, cst_t1973_dr1, cst_t1973_dr2, dr_id


@patch('classes.DataStructures.DataRowResult.get_now', new=Mock(return_value='1'))
class DataStructureTests(unittest.TestCase):

    def test_data_structure_jsonate(self):
        dre = DataRowResult(**cst_t1973_dr1)
        dre.update(testscript_steps_id_list=[1, 2, 3])
        expected = '[{\"id\": 1, \"testResultStatusId\": 930, \"executionDate\": \"1\"}, ' \
                   '{\"id\": 2, \"testResultStatusId\": 930, \"executionDate\": \"1\"}, ' \
                   '{\"id\": 3, \"testResultStatusId\": 930, \"executionDate\": \"1\"}]'
        self.assertEqual(expected, dre.jsonate())

    def test_test_case_execution_jsonate(self):
        dr = DataRowResult(**cst_t1973_dr1)
        init = cst_t1973_tce
        init.update(data_row_results=dr)
        tce = TestCaseExecution(**init)
        dr2 = DataRowResult(**cst_t1973_dr2)
        tce.update(data_row_results=dr2)
        init.update(data_row_results=[dr.dictate(), dr2.dictate()],
                    has_data_rows=True)
        expected = json.dumps(init, default=DataRowResult.jsonate)
        self.assertEqual(len(tce.data_row_results), 2)
        self.assertEqual(expected, tce.full_jsonate())
        print(tce.jsonate())

    def test_test_execution_results(self):
        status_codes = [dict({'id': 1, 'name': 'pass'}),
                        dict({'id': 2, 'name': 'fail'})]
        ter = TestsExecutionResults(status_codes)
        tce = TestCaseExecution(**cst_t1973_tce)
        tce.status = 'Pass'
        dr1 = DataRowResult(**cst_t1973_dr1)
        tce.update(data_row_results=dr1)
        self.assertFalse(tce.has_data_rows)
        args = None, 'testcase', 'fail', 'logfile', 'filename', '1000', 1
        args0 = None, 'testcase', 'fail', 'logfile1', 'filename', '2000', 0
        ter.add_result(*args0)
        ter.append(tce)
        ter.add_result(*args)
        self.assertEqual(len(ter), 2)
        self.assertEqual(len(ter[0].data_row_results), 2)
        self.assertEqual(tce.status, 'Fail')
        print(ter)
        print('------------')
        print(tce)

    def test_zip_with_id(self):
        expected_1 = [{'index': 0,
                       'parameterSetId': 1,
                       'testResultStatusId': 0,
                       'executionDate': '1',
                       'log_file': '',
                       'xml_file': ''},
                      dict({'index': 0, 'parameterSetId': 2, 'testResultStatusId': 0, 'executionDate': '1', 'log_file': '', 'xml_file': ''})]
        expected_2 = [dict({'index': 0, 'parameterSetId': 1, 'testResultStatusId': 0, 'executionDate': '1', 'log_file': '', 'xml_file': ''}),
                      dict({'index': 0, 'parameterSetId': 2, 'testResultStatusId': 0, 'executionDate': '1', 'log_file': '', 'xml_file': ''}),
                      dict({'index': 0, 'parameterSetId': 3, 'testResultStatusId': 0, 'executionDate': '1', 'log_file': '', 'xml_file': ''}),
                      dict({'index': 0, 'parameterSetId': 4, 'testResultStatusId': 0, 'executionDate': '1', 'log_file': '', 'xml_file': ''})]
        dr1 = DataRowResult(parameterSetId=1)
        dr2 = DataRowResult(parameterSetId=2)
        dr3 = DataRowResult(parameterSetId=3)
        dr4 = DataRowResult(parameterSetId=4)
        tce = TestCaseExecution(**cst_t1973_tce)
        tce.update(data_row_results=dr1)
        tce.update(data_row_results=dr2)
        print(tce)
        print('---------------')
        tce.zip_with_id(dr_id)
        print(tce)
        print('---------------')
        print(tce.jsonate())
        print('===============')
        #self.assertListEqual(tce.data_row_results, expected_1)
        tce.update(data_row_results=dr3)
        tce.update(data_row_results=dr4)
        tce.zip_with_id(dr_id)
        #self.maxDiff = None
        #self.assertListEqual(tce.data_row_results, expected_2)
        print(tce)
        print('---------------')
        print(tce.jsonate())


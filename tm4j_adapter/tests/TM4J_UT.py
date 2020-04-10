import unittest
from classes.TM4J import TM4J, strip_none_values
from classes.DataStructures import TestCaseExecution
from libs.config import read_config
from tests.TestData.tmconnect.prefilled_tm4j_items import jira_issue, jira_issues, cst_t1973_tce_dr
from tests.config import tm_config


class BaseTm4jUT(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parseconfig = read_config(tm_config['configPath'])
        cls.tm = TM4J(tm_config['configPath'])

    def test_create_testrun_with_linked_issues(self):
        key = self.tm._post_new_testcycle(name='UT-testcycle',
                                          linked_issues=jira_issues)
        self.assertIsNotNone(key)
        self.tm._delete_testrun(key=key)

    def test_get_jira_internal_id(self):
        jira_id = self.tm._get_jira_issue_id(jira_issue[0])
        self.assertEqual(int(jira_id), 986190)

    def test_get_tr_iid(self):
        self.tm.testrun['key'] = 'CST-C7'
        iid = self.tm._get_tr_id()
        self.assertEqual(iid, 677)
    
    def test_strip_none_values(self):
        list_obj = [{'testRunId': 1625, 'issueId': '986190', 'typeId': 2}, 
                    {'testRunId': 1625, 'issueId': '941290', 'typeId': 2}]
        list_obj_res = '[{\"testRunId\": 1625, \"issueId\": \"986190", \"typeId\": 2}, ' \
                       '{\"testRunId\": 1625, \"issueId\": \"941290\", \"typeId\": 2}]'
        dict_obj = {'testRunId': 1625, 'issueId': '941290', 'typeId': 2}
        dict_obj_res = '{\"testRunId\": 1625, \"issueId\": \"941290\", \"typeId\": 2}'
        other_obj = 123
        other_obj_res = '123'
        self.assertEqual(strip_none_values(list_obj), list_obj_res)
        self.assertEqual(strip_none_values(dict_obj), dict_obj_res)
        self.assertEqual(strip_none_values(other_obj), other_obj_res)

    def test_get_testcase_run_id(self):
        self.tm.testrun['key'] = 'CST-C16'
        iid = self.tm._get_testcase_run_id('CST-T1544')
        self.assertEqual(iid, 40078)

    def test_get_datarow_ids(self):
        run_id = '32793'
        self.tm._tr_internal_id = '1257'
        expected = {6697: [288543], 6698: [288544], 6699: [288545], 6700: [288546], 6701: [288547], 6702: [288548], 6703: [288549], 6704: [288550], 6705: [288551], 6706: [288552]}
        self.assertDictEqual(self.tm._get_datarow_ids(run_id), expected)
        print(self.tm._get_datarow_ids(run_id))

    def test_post_data_driven_test_results(self):
        tce = TestCaseExecution(**cst_t1973_tce_dr)
        tr_key = self.tm.find_testcycle(name='UT-testcycle')
        tce.test_cycle_key = tr_key
        self.tm.post_data_driven_test_results(tce)

    def test_post_test_results(self):
        tr_key = self.tm.find_testcycle(name='UT-testcycle')
        self.tm.find_testcase(key='CSR-T801')
        self.tm.post_test_result(test_cycle_key=tr_key, status='Pass', environment='PPR', executed_by='pyakovlev')

    def test_delete_testrun(self):
        testruns = ['CST-C66']
        for item in testruns:
            self.tm._delete_testrun(item)

    def test_delete_testcase(self):
        testcases = ['CSR-T907']
        for item in testcases:
            self.tm._delete_testcase(item)

    def test_tc_iid(self):
        self.tm.testcase['key'] = 'CST-T1973'
        print(self.tm._get_tc_id())

    def test__put_testcase_paramtype_property(self):
        self.tm.find_testcase(key='CST-T278')
        self.tm._put_testcase_paramtype_property()


class Tm4jUT(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parseconfig = read_config(tm_config['configPath'])
        cls.tm = TM4J(tm_config['configPath'])

    def test_update_test_script(self):
        from libs.multi_threading import run_threaded

        def patch_testcase(key):
            tm = TM4J(tm_config['configPath'])
            tm.find_testcase(key=key)
            print(f'Updating {key}')
            tm._put_testcase_paramtype_property()

        testcases = [x['key'] for x in self.tm._get_all_project_testcases()]
        run_threaded(testcases, patch_testcase, None)

    def test_attach_testcase_step_file(self):
        id = 360509
        path = 'C:\\Users\\pyakovlev\\CS-SQA\\common-test\\tm4j_adapter\\tests\TestData\\tmconnect\\1.log'
        self.tm.attach_testcase_step_file(id, path)

    def test_find_testcase(self):
        key = self.tm.find_testcase(name=': Only Doctor shall be able to restart case ')
        print(key)

    def test_add_new_env(self):
        self.tm._check_environment("new_env")

    def test_propagation(self):
        qwargs = dict({'status': 'Pass',
                       'environment': 'qas',
                       'executed_by': 'tfenwick',
                       'script_results': None,
                       'comment': None,
                       'test_cycle_key': 'CSR-C14',
                       'issue_links': None,
                       'execution_time': '1102'})
        self.tm.find_testcase(key='CSR-T826')
        self.tm.post_test_result(**qwargs)


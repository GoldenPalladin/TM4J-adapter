from unittest.mock import Mock, create_autospec, PropertyMock
from classes import TM4J
from tests.TestData.tmconnect.prefilled_tm4j_items import testcase_full, testrun_full

mocked_tm4j = create_autospec(TM4J.TM4J)
mocked_tm4j.find_testcase = Mock(return_value='CST-T1')
type(mocked_tm4j).testcase = PropertyMock(return_value=testcase_full)
mocked_tm4j.update_testcase = Mock()
mocked_tm4j.add_testcase_weblink = Mock()
mocked_tm4j.find_testcycle = Mock(return_value='CST-R1')
type(mocked_tm4j).testrun = PropertyMock(return_value=testrun_full)
mocked_tm4j.post_test_result = Mock()
mocked_tm4j.post_data_driven_test_results = Mock()
mocked_tm4j.attach_testcase_result_file = Mock()


exc_mocked_tm4j = create_autospec(TM4J.TM4J)
mocked_tm4j.find_testcase = Mock(side_effect=Exception)


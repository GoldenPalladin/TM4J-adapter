from typing import List
from itertools import chain
import datetime
import json


class DataRowResult(object):
    """
    Class corresponds to test execution for one data row (data set)
    for data-driven tests (examples table in BDD)
    """
    def __init__(self, **kwargs):
        self.index = 0                          # rocs execution index from '... -- @1.x' naming
        self.parameterSetId: int = 0            # ParameterSet = data row in data table
        self.testResultStatusId: int = 0        # UI statuses ID unique per project
        self.executionDate = self.get_now()
        self.log_file: str = ''                 # log file path
        self.xml_file: str = ''                 # junit xml file path
        self.is_failed = False                  # is test execution failed
        self.testscript_steps_id_list = list()  # list of testscript steps id (one or more for test containing one or more steps)
        self.update(**kwargs)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if type(other) is type(self):
            self_properties = {k: v for k, v in self.__dict__.items() if k not in ['log_file', 'xml_file']}
            other_properties = {k: v for k, v in other.__dict__.items() if k not in ['log_file', 'xml_file']}
            return self_properties == other_properties
        return False

    @staticmethod
    def get_now():
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def update(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def dictate(self) -> list:
        return [dict(id=step_id,
                     testResultStatusId=self.testResultStatusId,
                     executionDate=self.executionDate) for step_id in self.testscript_steps_id_list]

    def jsonate(self) -> str:
        return json.dumps(self.dictate())


class TestCaseExecution(object):
    """
    Class corresponds to full testcase execution for all data rows
    """
    def __init__(self, **kwargs):
        self.key = None
        self.name = None
        self.test_cycle_key = None
        self.status = None
        self.environment = None
        self.comment = None
        self.assignedTo = None
        self.executedBy = None
        self.executionTime: int = 0
        self.data_row_results: List[DataRowResult] = list()
        self.has_data_rows: bool = False
        self.update(**kwargs)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def __getitem__(self, item):
        return self.data_row_results[item]

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def update(self, **kwargs):
        for key in kwargs:
            if key == 'data_row_results':
                if isinstance(kwargs[key], dict):
                    kwargs[key].update(index=(len(self.data_row_results)))
                    self.data_row_results.append(DataRowResult(**kwargs[key]))
                elif isinstance(kwargs[key], DataRowResult):
                    kwargs[key].update(index=(len(self.data_row_results)))
                    self.data_row_results.append(kwargs[key])
                elif isinstance(kwargs[key], list):
                    for item in kwargs[key]:
                        self.update(data_row_results=item)
            else:
                setattr(self, key, kwargs[key])
        self.has_data_rows = len(self.data_row_results) > 1 or \
                             (len(self.data_row_results) == 1 and self.data_row_results[0].index > 0)  # if any data row has positive index
        self.status = 'Fail' if True in (result.is_failed for result in self.data_row_results) else 'Pass'

    def dictate(self):
        dd_results = [x.dictate() for x in self.data_row_results]
        result = {k: v for k, v in self.__dict__.items() if v is not None}
        result.update({'data_row_results': dd_results})
        return result

    def full_jsonate(self) -> str:
        return json.dumps(self.dictate(), default=DataRowResult.jsonate)

    def jsonate(self) -> str:
        return json.dumps(list(chain(*[x.dictate() for x in self.data_row_results])), default=DataRowResult.jsonate)

    def get_files_list(self) -> list:
        return [(x.xml_file, x.log_file) for x in self.data_row_results]

    def zip_with_id(self, datarow_ids: dict):
        zipped = list(zip(self.data_row_results, datarow_ids))
        [data_row.update(testscript_steps_id_list=datarow_ids[ps_id], parameterSetId=ps_id)
         for data_row, ps_id in zipped]


class TestsExecutionResults(list):
    """
    Class corresponds to list of testcase executions in project
    needs project status codes form https://jira.aligntech.com/rest/tests/1.0/project/{project_id}/testresultstatus
    """
    def __init__(self, status_codes: json):
        super().__init__()
        self.json_codes = status_codes                                  # per project  status codes json
        self.status_codes = {x['name']: x['id'] for x in status_codes}  # name: id status codes dict

    def __str__(self):
        return str([str(x) for x in self])

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(key)
        elif isinstance(key, slice):
            ter = TestsExecutionResults(self.json_codes)
            start = key.start if key.start else 0
            stop = key.stop if key.stop else (-1)
            step = key.step if key.step else 1
            for i in range(start, stop, step):
                ter.append(self[i])
            return ter
        else:
            raise TypeError('Index must be int, not {}'.format(type(key).__name__))

    def append(self, item: TestCaseExecution) -> None:
        if not isinstance(item, TestCaseExecution):
            raise TypeError(f'item is not of type {type(TestCaseExecution)}')
        super(TestsExecutionResults, self).append(item)

    def set_testrun_key(self, key: str):
        for result in self:
            result.update(test_cycle_key=key)

    def add_result(self, *args) -> TestCaseExecution:
        """
        (testcase_key, testcase_name, testcase_status, logfile, filename, testcase_execution_time, testcase_example_row)
        :param args:
        :return:
        """
        testcase_key, testcase_name, testcase_status, logfile, xml_file, testcase_execution_time, testcase_example_row = args
        dr = DataRowResult(log_file=logfile,
                           xml_file=xml_file,
                           index=testcase_example_row,
                           testResultStatusId=self.status_codes[testcase_status],
                           is_failed=(testcase_status == 'Fail'))
        try:
            tce = [x for x in self
                   if ((testcase_key is not None and x.key == testcase_key) or (x.name == testcase_name))][0]
            tce.executionTime += int(testcase_execution_time)
        except IndexError:
            tce = TestCaseExecution(key=testcase_key,
                                    name=testcase_name,
                                    executionTime=int(testcase_execution_time))
            self.append(tce)
        tce.update(data_row_results=dr)
        return tce



testcase_full = {
    "key": "CST-T1",
    "projectKey": "CST",
    "name": "Ensure the axial-flow pump is enabled",
    "precondition": "The precondition.",
    "objective": "The objective.",
    "folder": "/Orbiter/Cargo Bay",
    "status": "Approved",
    "priority": "Low",
    "owner": "qaautobot",
    "estimatedTime": 138000,
    "labels": ["Smoke", "Functional"],
    "issueLinks": ["JQA-123", "JQA-456"],
    "parameters": {
        "variables": [
            {
                "name": "Initial Pressure",
                "type": "FREE_TEXT"
            },
            {
                "name": "High Pressure",
                "type": "FREE_TEXT"
            }
        ],
        "entries": [
            {
                "Initial Pressure": "10",
                "High Pressure": "3000"
            },
            {
                "Initial Pressure": "20",
                "High Pressure": "6000"
            }
        ]
    },
    "testScript": {
        "type": "STEP_BY_STEP",
        "steps": [
            {
                "index": 0,
                "description": "Ignite the secondary propulsion engines.",
                "testData": "Combustion chamber's initial pressure: <span class=\"atwho-inserted\">{Initial Pressure}</span>",
                "expectedResult": "Ensure the high-pressure combustion chamber's pressure is around <span class=\"atwho-inserted\">{High Pressure}</span> psi."
            }
        ]
    }
}


testrun_full = {
    "executionResultsSummary": {
        "Pass": 1,
        "Fail": 1
    },
    "key": "CST-R1",
    "projectKey": "JQA",
    "name": "Full regression",
    "status": "Done",
    "iteration": "Sprint 1",
    "folder": "/root folder/child folder",
    "version": "1.1.0",
    "issueKey": "CST-1",
    "owner": "admin",
    "plannedStartDate": "2016-02-24T08:10:59.514Z",
    "plannedEndDate": "2016-02-26T12:00:00.000Z",
    "estimatedTime": 2338000,
    "executionTime": 150000,
    "testCaseCount": 2,
    "issueCount": 1,
    "items": [
        {
            "id": 500020,
            "testCaseKey": "CST-T1",
            "environment": "Chrome",
            "userKey": "vitor.pelizza",
            "executionDate": "2017-05-16T16:42:06.000Z",
            "status": "Fail",
            "executedBy": "vitor.pelizza",
            "assignedTo": "cristiano.caetano",
            "plannedStartDate": "2016-02-10T19:22:00-0300",
            "plannedEndDate": "2016-02-12T19:22:00-0300",
            "actualStartDate": "2016-02-12T19:22:00-0300",
            "actualEndDate": "2016-02-14T19:22:00-0300",
            "customFields": {
                "single choice": "Propulsion engines",
                "multichoice": "Brazil, England"
            }
        },
        {
            "id": 500021,
            "testCaseKey": "CST-T2",
            "environment": "Firefox",
            "executionDate": "2017-05-16T16:31:28.000Z",
            "status": "Pass"
        }
    ]
}

"""
927 - Not executed
928 - Skipped
929 - Passed
930 - Failed
931 - Blocked
"""

stg_jira_issues = ['']
jira_issues = ['CST-100', 'CST-101']
jira_issue = ['CST-100']

cst_t1973_tce = dict(key='CST-T1973',
                     name='CST-T1727_This is test scenario to check tm4j updater',
                     status='Fail',
                     executionTime=12500)
cst_t1973_dr1 = dict(parameterSetId=41,
                     testResultStatusId=930,  # is_failed
                     is_failed=True,
                     log_file='C:\\Users\\pyakovlev\\CS-SQA\\common-test\\tm4j_adapter\\tests\TestData\\tmconnect\\1.log')
cst_t1973_dr2 = dict(parameterSetId=41,
                     testResultStatusId=929,  # passed
                     is_failed=False,
                     log_file='C:\\Users\\pyakovlev\\CS-SQA\\common-test\\tm4j_adapter\\tests\TestData\\tmconnect\\2.log')
cst_t1973_tce_dr = cst_t1973_tce.copy()
cst_t1973_tce_dr.update(data_row_results=[cst_t1973_dr1, cst_t1973_dr2])

dr_id = dict({9543: [295935, 295934], 9544: [295937, 295936], 9545: [295939, 295938]})




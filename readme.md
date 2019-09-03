# TM4J-adapter
API connector to manage testcases and testcycles in Adaptavist for Jira (TM4J).

Configurable. Dockerable. Bambooable.

Can parse JUnit reports into test results, Behave .feature files into testcases

[parseconfig]: ""
# Configuration file parseconfig.ini

**Note:** Boolean flags are string-compared to 'True' so they should take **True** value (first letter capitalized). Any other value is considered as **False**.


    [GENERAL]
    tm4jUrl = 
    tm4jLogin = 
    tm4jPassword = 
    tm4jProjectKey = CSX
    tcFolder = NEwFolder1984
    trFolder = JUnitTests
    
    [NOTFOUND]
    createTestcase = True
    createTestrun = True
    createStep = True
    createTcFolder = True
    createTrFolder = True
    
    [BDD]
    featuresFolder = \bdd_features
    parseFolder = True
    featuresFile = validation_errors.feature
    repoLink = 
    parseJiraTags = False
    
    [JUNIT]
    env = cs1
    reporter = pyakovlev
    testcycleName = "123"
    pathToArtifact = artifacts/artifacts.zip
    junitFolder = artifacts
    parseFolder = False
    junitFile = artifacts/junit.xml
    pathToLogs = artifacts/testLogFile.log
    
    [LOGGING]
    logTcCreation = True
    logTcCreationPath = logs\CreatedTestCases.csv
    splunkHost = 
    splunkPort = 443
    splunkToken = xxxxxxx-xxx-xxx-xxxx-xxxx
    splunkINdex = main

[dps]: ""
# Data parsing scripts
## junit_parser.py
Library implements parsing junit reports into TM4J testruns and testresults.

#### Options:
Configured by section **[JUNIT]** in parseconfig.ini
 
* **pathToLogs** -- if set, file is parsed as log file (all lines containing 'test' are considered 
as test names and all lines between are considered as log data to be inserted in step execution notes). 
Log file is parsed by *test_log_parser.py* library

* **env, reporter** -- data to be inserted in testrun fields

* **testcycleName** -- name of the TestCycle to append results. If doesn't exist -- will be created
(configured in **[NOTFOUND]** section of config file)

* **parseFolder** -- if set to True, every .xml file in **junitFolder** will be parsed as junit report.

* **junitFile** -- path to single junit report file.

jnit_parser.py can use runtime parameters -- if set, they have higher priority than ones from config file. 
They are:


        -n, --tc_name, help="Test cycle name"
        -f, --j_file, help="Path to junit.xml"
        -o, --j_folder, help="Path to folder with junit results"
        -l, --logs, help="Path to test execution logs"

## json_parser.py
Library implements parsing json reports into TM4J testruns and testresults.

JSON reports should have the following format:

    {
    "projectKey": "SIS", 
    "testCaseKey": "SIS-T200",
    "status": "Pass", 
    "comment": "pid:9893018", 
    "executedBy": "dvallabhuni",
    "scriptResults": [  {"index": 0, "status": "Pass", "comment": "XX"}, 
                        {"index": 1, "status": "Pass", "comment": "XX"}]
    }

#### Options:
Configured by section **[JSON]** in parseconfig.ini
 
* **env, reporter** -- data to be inserted in testrun fields

* **testcycleName** -- name of the TestCycle to append results. If doesn't exist -- will be created
(configured in **[NOTFOUND]** section of config file)

* **parseFolder** -- if set to True, every .json file in **jsonFolder** will be parsed as junit report.

* **jsonFile** -- path to single junit report file.

json_parser.py can use runtime parameters -- if set, they have higher priority than ones from config file. 
They are:

        -n, --tc_name, help="Test cycle name"
        -f, --j_file, help="Path to junit.xml"
        -o, --j_folder, help="Path to folder with junit results"
        
## bdd_parser.py
Library to import BDD feature files into TestCases


#### Options:
Configured by section **[BDD]** in parseconfig.ini

* **parseFolder** -- if set to True, every .xml file in **featuresFolder** will be parsed
* **featuresFile** -- separate .feature file to import
* **repoLink**  -- not implemented yet
* **parseJiraTags** -- if True, all scenario tags like XXX-### will be parsed and inserted
as linked issues


## post_testrun.py
Script to parse rocs2 results stored as artifacts.zip

# Bamboo
Parsing results 

First of all do set up Bamboo variables like described below -- define location of JUnit reports, 
test logs, feature files, etc. within Bamboo runner workspace.

Job to post results consists of the following tasks:

* **Source Code Checkout** to get latest tmconnector script 

*(NOTE: everything will be downloaded into **/tm4j-adapter** directory)*
* **Artifact download** to get test results from test execution Bamboo plan 
if you use external plan to post results 

(*NOTE: make sure artifacts are made shared in this plan
and are correctly placed inside **/tm4j-adapter** folder*)
* **Script** grep bamboo variables to file using Shell script:
 
     
    env | grep ^bamboo_ > bamboo_env_file
(*NOTE: file name is hardcoded, so don't change it!*)
* **Docker -> Run a Docker container** with installed requirements and Python 3.7 
 and use *bamboo_runner.py* in docker to start one of the 
 [data parsing scripts][dps] in Docker with option --script/-s:


    /bin/sh "python bamboo_runner.py -s junit_parser"
(*NOTE: Don't forget to mount ${bamboo.working.directory}/tm4j-adapter/
inside the Docker container*)
## Bamboo variables
Initially script is parameterized by [parseconfig.ini][parseconfig].
You can override any parameter by specifying Bamboo variable in format like:

 **SECTION_NAME.parameterName=value**

where section name and parameter name must correspond to those in parseconfig.ini

# tmconnect.py
Library to use TM4J API methods with Python.

Can be configured via [parseconfig.ini][parseconfig] file

Implements three classes:

* TM4J -- main class to work with TestManagement for Jira, in self stores configs, testcase
and testrun information in json format
* TestScript -- class to work with testcase testscript (steps)
* TestParameters -- class to work with test parameters to create data-driven testcases.

More info in code.

#### Options:
Configured by the following sections in parseconfig.ini:

Section **[GENERAL]** 
* **tm4jUrl, tm4jLogin, tm4jPassword** -- url and credentials to connect to tm4j
* **tm4jProjectKey** -- key of project to work with
* **tcFolder** -- folder to create TestCases in
* **trFolder** -- folder to create TestCycles in

Section **[NOTFOUND]**

Configures auto-creation of the objects, that are not found in the system. 
If set to True, object will be created, otherwise an exception will be raised.
* **createTestcase** -- create TestCase 
* **createTestrun** -- create TestCycle
* **createStep** -- create TestCase step
* **createTcFolder** -- create TestCase folder
* **createTrFolder** -- create TestCycle folder

Section **[LOGGING]**
* **logTcCreation** -- if True, all created testcases will be logged with keys in 
**logTcCreationPath** .csv file
* **splunkHost, splunkPort, splunkToken, splunkIndex** -- connection properties 
to use Splunk logging

Supposed usage sequence:

    tm4j = TM4J()                                               initialise objects
    ts = TestScript()
    tp = TestParameters()
    tm.find_testcase('testrun', "Test run name")
        for test in testsuite:
            tm.find_testcase('testcase', name, None, folder)    find_testcase a testcase by name (will be created if none is found)
            ts = TestScript()
            if 'testScript' in tm.testcase:                     check if testcase already has steps
                ts.script = tm.testcase['testScript']           read it
            table = test_data_source                            get test data (i.e. from scenario outline)
            tp.set_variables(table.headings)                    initialise data variables
            for row in table.rows:
                tp.append_values(row.headings, row.cells)       add variable:value pairs
            testcase.update({'parameters': tp.parameters})
            for step in steps:  
                ts.set_step_results(name, status, comment)      add steps to test script
            tm.testcase['testScript'] = ts.script               
            tm.update_testcase(updated_values)                                update testcase
            tm.post_test_result('Pass', tm.config['RESULTS']['env'], tm.config['RESULTS']['reporter'], ts.results)

## TM4J methods
### find_testcase(self, name: str, key: str = None, folder: str = None)
    
Search method for test run or test cases. If no result found, new item is created.
Found testcase is stored in *self.testcase* parameter.

        :param name: name of the testcase to search
        :param key: if specified, search by key only, name is ignored
        :param folder: if specified, search in folder; 
        If None, config folder will be used
        if no item found, it will be created in this folder.
        Folder should be specified in "parent folder" or "parent folder/child folder"
Folder should be specified in "/parent folder" or "/parent folder/child folder" format

### update_testcase
*(self, updated_values: json)*

Updates testcase according to parameters

### post_testcase_from_json
*(self, testcase: json) -> str*

creates testcase directly from json

    :param testcase: json-formatted testcase. See https://docs.adaptavist.io/tm4j/server/api/v1/
    :return testcase key"""
    
### find_testrun
*(self, name: str, folder: str = None)*

Search method for one or more test cycles. Search by testcycle name. 
If no result found, new item is created. Found testcycle is stored in *self.testrun* parameter

    :param name: name of the item to search
    :param folder: if specified, search in folder; 
    If None, config folder will be used
    If no item found, it will be created in this folder.
    Folder should be specified in "parent folder" or "parent folder/child folder" format

### post_new_testrun
*(self, name: str, folder: str = None, linked_issue: str = None, check_config: bool = False)*

Creates new testcycle. Created testcycle is stored in *self.testrun* parameter

    :param name: testcycle name
    :param folder: testcycle folder. If None, config folder will be used.
    Folder should be specified in "parent folder" or "parent folder/child folder" 
    :param linked_issue: linked Jira issue
    :param check_config: is passed from find_testrun method to check if
    auto creation of not-found is allowed
    

### post_test_result
*(self, status: str, environment: str, executed_by: str, script_results: json = None, comment: str = None)*
      
Creates test execution result in current testcycle and testcase for specified status, 
executor and env

    :param status: testcase execution status. Auto set to Fail if any step is Fail.
    :param environment: env parameter. Must correspond to one in TM4J settings
    :param executed_by: name of person executed tests
    :param script_results: json with steps execution results
    :param comment: comment to testcase execution

### attach_testrun_file
*(self, file_path: str)*

Attach file to TestCycle execution. Must have value of *self.testrun['key']* 
-- create TestCycle beforehand.

### attach_testcase_result_file
*(self, file_path: str)*

Attach file to TestCase execution. Must have value of *self.__testResultsId* 
-- call post_new_testrun beforehand.
      
## TestScript methods
Class to deal with testscript created on test steps

testScript json structure is created in *self.script*, 
see https://docs.adaptavist.io/tm4j/server/api/v1/

### append_step
*(self, description: str, test_data: str, expected_result: str)*

Appends step to steps list

    :param description: step description
    :param test_data: step test data
    :param expected_result: step expected result
    
### set_step_results
*(self, description: str, status: str, comment: str)*

Finds step by name and set step execution result

    :param description: step name
    :param status: step execution ststus
    :param comment: execution comment

## TestParameters methods
class to deal with test parameters 

### set_variables
*(self, names: list)*
initiate variables list

    :param names: list of parameter names

### append_values
*(self, variables: list, values: list)*

method to add parameter:value string to testcase definition

    :param variables: list of parameter names
    :param values: list of parameter values
    
# Additional library files
### files.py
Functions to perform files operations

### test_log_parser.py
Parse txt test log to grep test execution data

### tm_log.py
Logging extensions and configuration

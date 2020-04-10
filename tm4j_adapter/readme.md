# TM4J-adapter

[Teams channel with updates and news](https://teams.microsoft.com/l/channel/19%3ad4ae6faf75584043aa1fa4d45574f40e%40thread.skype/CS%2520TM4J?groupId=8d5cb294-9c97-4338-b5b0-5f4906774184&tenantId=9ac44c96-980a-481b-ae23-d8f56b82c605)
## Intro

First of all to get access to TestManagement plugin in Jira you should
pass [the learning course](https://aligntechnology.sabacloud.com/Saba/Web_spf/NA1PRD0028/app/shared;spf-url=common%2Fledetail%2Fcours000000000027593)

**With tm4j-adapter you can do the following:**

- import bdd tests into tm4j from feature files
- log created testcases into csv file (key, name, any additional info)
- update scenario name with testcase keys in feature file(s) during 
bdd-parser test importing or later from csv log
-automatically parse test tags and for Jira ticket tag automatically create 
link to Jira issue
- parse test execution results from junit report, from rocs artifact.zip
or from json
- create not found testcases and testcycles
- embed adapter in Bamboo plan and configure it by Bamboo variables

## Quick start
### Config setup
- Open *configuration.ini* and Goto *[GENERAL]* section 
- Check *tm4jUrl* -- if it points to correct Jira instance
- Check credentials
- Update *tm4jProjectKey* to work with project you need 
- Update *tcFolder* to set folder where **TestCases** will be searched/created
- Update *trFolder* to set folder where **TestCycles** will be searched/created
- See errors in *error.log*

### Tests import

- checkout latest tests from repo
- set up BDD section in config in a way like this:

        [BDD]
        localRepoRoot = C:\Users\pyakovlev\CS-SQA\common-test\tm4j_adapter\test_repo
        featuresFolderInLocalRepository = api_test_gallery_bdd/features/tests
        diffTestsUpdate = False
        parseFolder = True
        copyFolderStructure = True
        repoLink = {link to repo to link exported tests}
        parseJiraTags = True
        updateFeatureFileOnExport = True
        
- run **bdd_parser.py**, check *error.log* just in case
- commit and push updated .feature files back to repo 
(see TestCase keys section for details)

### Results posting

- run updated test from repo in rocs/bamboo
- download **artifacts.zip** somewhere or set up config.ini
to download artifact from Bamboo run
- set up EXECUTION & ROCS sections in the following way:

        [EXECUTION]
        env = PPR 
        reporter = pyakovlev
        testcycleName = {name for your testcycle}
        jiraTask = comma separated list of Jira tickets to link with testcycle
        
        [ROCS]
        pathToArtifact = artifacts\Gallery API.zip
        getResultsFromBamboo = False
        bambooBuildLink = https://bamboo.aligntech.com/browse/BDDCS-BTIAPR2-3382

- run **post_testrun.py**, see Testcycle number in concole log
- pozdravlayem, vy velikolepny!

## Details

If you need to:
- **import BDD scenarios** into TestCases -- use 
**bdd_parser.py**.
Don't forget to read the bdd_parser manual to set up **[BDD]** configuration
section to define path to .feature files (or the whole folder to import
all .feature files)and other import options.

- **import test results from Rocs2** (as *artifacts.zip* file) into 
TestCycles -- use **post_testrun.py**.
Read the post_testrun section to set up **[ROCS]** configuration
section to define path to artifacts.zip files and TestCycle name to post
 results into.

- **import test results from JUnit report** (as single *junit.xml* file) 
into TestCycles -- use **junit_parser.py**.
Look through the junit_parser manual to set up **[JUNIT]** 
configuration section path to *JUnit.xml* file (or the whole folder to import
all .xml files) and TestCycle name to post results into.

- **import test results from json-based test report** 
(as single *results.json* file) into TestCycles -- use **json_parser.py**.
Goto the json_parser manual to set up **[JSON]** 
configuration section path to *results.json* file (or the whole folder to import
all .json files) and TestCycle name to post results into.

### Files paths notes

Using option **General -> useRelativePath** you can set whether to treat 
all the paths in parseconfig.ini as relative or absolute.

Absolute paths are useful for local usage.

Relative paths are useful inside a Docker container.
They are based on *tm4j-adapter* directory,
so before using any artifacts from the outer world make sure to copy them
somewhere inside the base directory.


### Importing tests
Tests must be imported into TM4J in proper way -- with all steps, 
expected results and all the things described in appropriate Align docs.
At the moment implemented parser for bdd .feature files that support
all proper test details importing. One can use it as an example to 
implement its own tests parser.

*Note: you can immediately post test execution results without any tests
created. In this case empty tests (name only) will be created for further
update.*

### Logging tests creation
There is a separate logger that logs creation of testcases into csv file.
It saves Key, Name and any additional info (*logger_args* parameter in 
*find_testcase* method). For bdd-parser we save path to feature file.
This is made in order to save created test keys for further tests update.
Config section:

    [LOGGING]
    logTcCreation = True
    logTcCreationFolder = logs

File name is constructed as **{logTcCreationFolder}\\{tcFolder}.csv** 

### TestCase keys
Testcases can be searched by name or by key. Since name can be modified,
it is preferable to search by key -- so we need to store key info somewhere 
in automated tests. The most obvious and convenient way is to append key 
to test name like this: {key}{delimiter}{name}

On every search by name tmconnect.py checks if first part of name is like
testcase key and if so, it will search by key.

Keys can be appended automatically by **update_tests_with_keys.py** for
bdd feature files (from .csv creation log). Or if **BDD -> updateFeatureFileOnExport = True**
scenario names in feature file will be updated with keys automatically 
during tests export. Don't forget to commit changes back to repo.

More detailed is described on [dedicated wiki page](https://wiki.aligntech.com/display/CLWEB/TM4J+in+deployment+process)

[parseconfig]: ""
# Configuration file parseconfig.ini

**Note:** Boolean flags are string-compared to 'True' so they should take **True** value (first letter capitalized). Any other value is considered as **False**.


    [GENERAL]
    tm4jUrl = https://stgjira.aligntech.com/rest/atm/1.0
    tm4jLogin = qaautobot
    tm4jPassword = Aligner5
    tm4jProjectKey = CST
    tcFolder = BddParser
    trFolder = ParsersCycle
    useRelativePath = True
    testCaseKeyDelimiter = _
    threadsQty = 5
    
    [NOTFOUND]
    createTestcase = True
    createTestrun = True
    createStep = True
    createTcFolder = True
    createTrFolder = True
    
    [BDD]
    repoLink = https://src.aligntech.com/projects/CSSQA/repos/protocol/browse/api_tests_protocol_bdd
    #web link for root folder of feature files
    localRepoRoot = bdd_tests
    featuresFolderInLocalRepository = CS-SQA_tm4j\features\tests
    diffTestsUpdate = True
    diffFilePath = diff_file.log
    copyFolderStructure = True
    parseJiraTags = True
    tagsToExclude = obsolete, excluded
    updateFeatureFileOnExport = True
    
    [EXECUTION]
    env = PPR
    reporter = pyakovlev
    testcycleName = JUnitParserThreaded7
    jiraTask = CST-1, CST-2
    
    [ROCS]
    pathToArtifact = artifacts\Gallery API.zip
    getResultsFromBamboo = False
    bambooBuildLink = https://bamboo.aligntech.com/browse/BDDCS-BTIAPR2-3382
    
    [JUNIT]
    junitPath = artifacts
    pathToLogs = artifacts/testLogFile.log
    
    [JSON]
    jsonPath = artifacts
    
    [LOGGING]
    configLevel = info
    logTcCreation = True
    logTcCreationFolder = logs
    splunkHost = http-inputs-align.splunkcloud.com
    splunkPort = 443
    splunkToken = xxx-xxx-xxx-xxx
    splunkIndex = main

# Data parsing scripts

## Test execution data
* **env, reporter** -- data to be inserted in testrun fields

* **testcycleName** -- name of the TestCycle to append results. If doesn't exist -- will be created
(configured in **[NOTFOUND]** section of config file)
## junit_parser.py
Library implements parsing junit reports into TM4J testruns and testresults.

#### Options:
Configured by section **[JUNIT]** in parseconfig.ini
 
* **pathToLogs** -- if set, file is parsed as log file (all lines containing 'test' are considered 
as test names and all lines between are considered as log data to be inserted in step execution notes). 
Log file is parsed by *test_log_parser.py* library

* **junitPath** -- path to folder or file. If folder, every .xml file
 in will be parsed and added to execution results list.

junit_parser.py can use runtime parameters -- if set, they have higher priority than ones from config file. 
They are:


        -n, --tc_name, help="Test cycle name"
        -f, --j_file, help="Path to junit.xml"
        -o, --j_folder, help="Path to folder with junit results"
        -l, --logs, help="Path to test execution logs"

[json_parser]:""
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

* **jsonPath** -- path to junit report file or folder. All the same as
for junit parser.

json_parser.py can use runtime parameters -- if set, they have higher priority than ones from config file. 
They are:

        -n, --tc_name, help="Test cycle name"
        -f, --j_file, help="Path to junit.xml"
        -o, --j_folder, help="Path to folder with junit results"

     
## bdd_parser.py
Library to import BDD feature files into TestCases.

*Note: bdd_parser can be run with alternative configuration file using 
runtime parameter. This is convenient when importing tests into various 
projects/folders*
    
    "-c", "--config", help="Path to alternative config file"


#### Options:
Configured by section **[BDD]** in parseconfig.ini

* **repoLink**  -- is used as root to construct direct link from Testcase
(in Traceability tab) to the parsed .feature file in repository. 
* **localRepoRoot** -- root folder to local copy of git repo
* **featuresFolderInLocalRepository** -- folder in local repo containing
feature files
* **diffTestsUpdate** -- if True, only updated feature files
enumerated in diff_file.log are parsed, else every .xml file 
in **featuresFolderInLocalRepository** will be parsed
* **diffFilePath** -- path to git diff file inside localRepoRoot
* **copyFolderStructure** -- if set to True, subfolders structure of *parseFolder*
is created in side *tcFolder* wherein testcases are imported.
* **parseJiraTags** -- if True, all scenario tags like XXX-### will be parsed and inserted
as linked issues
* **tagsToExclude** -- comma-separated list of tags to mark scenario as obsolete.
Scenario marked with any of this tags will be skipped (neither added nor updated
in TM4J)
* **updateFeatureFileOnExport** -- if set to True, scenario names in feature
file are updated with created testcase keys


*NOTE: 
1. Link is constructed as **repoLink + featuresFolderInLocalRepository + pathToFeatureFileInFolder** 
way, so make sure that it resembles to path to feature file inside the repo*
2. **featuresFolderInLocalRepository** is used as entry point for subfolders structure.
Subfolders are constructed as **tcFolder + relative path from entry point** way,
so setting options in this way:
    
    
    [GENERAL] 
    tcFolder = ClinicalAPI
    
    [BDD]
    featuresFolderInLocalRepository = bdd_features/api_tests_clinical_bdd/features/tests
    parseFolder = True
    copyFolderStructure = True
        
will give structure brief required structure like this:

        ClinicalAPI
            access_other_api
            create_patient
            delegation
            
while giving extra short *featuresFolder* parameter:
        
        [GENERAL]
        tcFolder = ClinicalAPI
       
        [BDD]
        featuresFolderInLocalRepository = bdd_features
        parseFolder = True
        copyFolderStructure = True
        
will result in unwanted extra subfolders in TM4J like this:

        ClinicalAPI
            api_tests_clinical_bdd
                features
                    tests
                        access_other_api
                        create_patient
                        delegation



[post_testrun]: ""
## post_testrun.py
Script to parse rocs2 results stored as artifacts.zip

## update_tests_with_keys.py
Script to update feature files with testcase keys from test creation log (.csv)
Make sure you have data in it.

# Bamboo

## Bamboo variables
Initially script is parameterized by *parseconfig.ini*.
You can override any parameter by specifying Bamboo variable in format like:

 **SECTION_NAME.parameterName=value**

where section name and parameter name must correspond to those in parseconfig.ini

## Auto updating tests in TM4J
BDD tests in repo should be updated with testcase keys, tests in TM4J
should be updated with latest changes in BDD tests.

One can set up automatic update of tests (labels, steps, links etc.) by 
triggering bdd_parser.py inside a Bamboo plan.
Example of such Bamboo plan: https://bamboo.aligntech.com/browse/BDDCS-TM4JUP

Process will be the following:
* One creates a pull request with new/updated test inside a repo with BDD tests
* Pull request triggers new branch creation and build of the plan
* In the build plan: pull request commits are checked out, bdd_parsed 
updates the tests in TM4J and feature files with testcase keys, 
* Updated feature files are commited and pushed back to the repo into
the branch pull request was created in. New commit updates the pull request
* Reviewers see new commit and merge the pull request

### Setting up Bamboo plan
1. Add or ask tooling to add your repo with BDD test into the pool of linked repos. Make sure 
to fit the following options for repo:

        [ ] Enable repository caching on remote agents
        [v] Fetch whole repository
        
2. Plan configuration -> Repositories -> Add **your_repo** and **SQA/common-test**.
**IMPORTANT! Make sure your_repo is first in the list to be plan's default repository -- 
otherwise updates will not be committed in proper place!**

3. Plan configuration -> Branches: 
        
        Create plan branch 
            (*) When pull reques is created
        Delete plan branch
            [v] After branch was deleted from repository 
                [ 1 ] days
            [v] After branch was inactivity in repository 
                [ 1 ] days
        Triggers
            > Custom trigger
            > Bitbucket Server repository triggered
            
4. Tasks for update tests job:

        Source code checkout
            Repository > SQA/common tests
        Script
            mkdir -p tm4j_adapter/bdd_tests
        Source code checkout
            Repository > your_repo
            Checkout Directory: tm4j_adapter/bdd_tests
        Script
            #!/bin/bash
            rm -f diff_file.log
            git diff --name-only {your_branch_of_stable_tests} --output=diff_file.log
            echo "=====CHANGED FILES IN BRANCH====="
            cat diff_file.log
            echo "=====END====="
            Working subdirectory: tm4j_adapter/bdd_tests
        Script
            env | grep ^bamboo_ > bamboo_env_file
            echo "=====BAMBOO PLAN VARIABLES====="
            cat bamboo_env_file
            echo "===== END ====="
            Working subdirectory: tm4j_adapter
        Script (debug to see files strusture on bamboo agent)
            echo "=====VIEW CONTENTS OF CURRENT ROOT====="
            ls -R | awk '
            /:$/&&f{s=$0;f=0}
            /:$/&&!f{sub(/:$/,"");s=$0;f=1;next}
            NF&&f{ print s"/"$0 }'
            echo "=====END====="
        Docker
            Command > Run a Docker container
            Container command: /bin/sh -c "cd t/; python bamboo_runner.py -s bdd_parser"
            Volumes: ${bamboo.working.directory}/tm4j-adapter/ <-> /t
        Script
            #!/bin/bash
            rm -f diff_file.log
            Working subdirectory: tm4j_adapter/bdd_tests
        Repository Commit
            Repository > Default Repository (your_repo)
            Commit message: tm4j tests updated on ${bamboo.buildTimeStamp}
        Script (debug to see the last commit -- if any feature file is updated)
            #!/bin/bash
            echo "=====VIEW COMMIT DETAILS====="
            git log -p -1
            echo "=====END====="
        Repository Push
            Repository > Default Repository (your_repo)
     
5. Plan configuration -> Variables: 

Make sure to set up directories in a proper way to be available in bamboo agent. 
Note the slash orientation!

        GENERAL.tm4jProjectKey = {your_project_name}
        GENERAL.tcFolder = {test_cases_folder_name}
        GENERAL.useRelativePath = True
        NOTFOUND.createTestcase = True
        BDD.repoLink = {your_repo_url}
        BDD.localRepoRoot = bdd_tests
        BDD.featuresFolderInLocalRepository = {some_path}/features/tests
        BDD.diffTestsUpdate = True
        BDD.diffFilePath = diff_file.log
        BDD.copyFolderStructure = True
        BDD.parseJiraTags = True
        BDD.updateFeatureFileOnExport = True

## Posting build test results into TM4J

Example of Bamboo plan is https://bamboo.aligntech.com/browse/BDDCS-CAPTCC-15. 

First of all do set up Bamboo variables like described above -- define location of JUnit reports, 
test logs, feature files, etc. within Bamboo runner workspace.

Job to post results consists of the following tasks:

* **Source Code Checkout** to get latest tmconnector script from [SQA/common-test](https://src.aligntech.com/projects/SQA/repos/common-test/browse/tm4j-adapter)

*(NOTE: everything will be downloaded into **/tm4j_adapter** directory)*
* **Artifact download** to get test results from test execution Bamboo plan 
if you use external plan to post results 

(*NOTE: make sure artifacts are made shared in this plan
and are correctly placed inside **/tm4j_adapter** folder*)
* **Script** grep bamboo variables to file using Shell script:
 
     
    env | grep ^bamboo_ > bamboo_env_file
(*NOTE: file name is hardcoded, so don't change it!*)
* **Docker -> Run a Docker container** with installed requirements and Python 3.7 from 
[docker-dev/pyakovlev/tm4j/tm4j-python](https://repo.aligntech.com/webapp/#/artifacts/browse/tree/General/docker-dev/pyakovlev/tm4j/tm4j-python)
 and use *bamboo_runner.py* in docker to start one of the 
 data parsing scripts in Docker with option --script/-s:


    /bin/sh "python bamboo_runner.py -s junit_parser"
(*NOTE: Don't forget to mount ${bamboo.working.directory}/tm4j_adapter/
inside the Docker container*)

# Code structure
For detailed reference see docstrings in code. Also almost every variable is typed 
to make it more clear.
## Classes
* **Parser** -- base class for parsers. Implements the following methods:
        
        _read_single_file (interface, must be overriden in child class
            to implement file reading logic)
        read_files
        _parse_contents (interface, must be overriden in child class
            to implement data transformation logic)
        _post_single_result (interface, must be overriden in child class
            to implement single data item posting into TM4J)
        do_export_results
        
        
* **ThreadedParser(Parser)** -- class to implement multithreaded posting results. Adds 
the following methods:

        do_export_results (overridden method to post single result in multithreading)
        
        manage_unposted_results (interface, must be overridden in child class
            to implement what to do with the results, that are failed to be posted)

* **BddParser(Parser), JsonParser(Parser), JunitParser(ThreadedParser), 
RocsParser(ThreadedParser)** -- classes to implement 
specific parsing logic.

* **DataStructures** -- class to implement TestsExecutionResults >=> TestCaseExecution >=>
 DataRowResult
where '>=>' means '...containing list of...' used in data-driven tests execution posting

* **BaseTm4j, TM4J** -- classes to implement tm4j API interactions


## How to

### Write your own parser
1. Inherit from Parser or ThreadedParser. 
2. Define file reading logic in _read_single_file method
3. Define file contents parsing logic in _parse_contents method -- which data to use and so on
4. Define results posting logic in _post_single_result. If you're using ThreadedParser, 
remember about concurrency and use new instance of tm4j
5. If required, define manage_unposted_results logic for ThreadedParser
6. See existing parsers for more reference

### Use data-driven results posting
1. In your parser _parse_contents method must return **TestsExecutionResults** object, 
which maintains the following structure:

        TestCycle <-> TestsExecutionResults
        TestCase <-> TestCaseExecution
        Data row test execution <-> DataRowResult
        
2. Use **DataStructure.TestsExecutionResults.add_result()** method to add data row 
execution results into **TestsExecutionResults** object.
3. Use **post_data_driven_test_results** to post your results
4. See RocsParser for more reference

### Tips and tricks:
* due to API restrictions, items name will be trimmed to 255 symbols (see libs.tags_parse_lib.clear_name)


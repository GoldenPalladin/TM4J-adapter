import tempfile
import logging
import logging.config
from zipfile import ZipFile
from xml.dom.minidom import parseString
from requests.exceptions import HTTPError
from tmconnect import TM4J, TM4JException
from tm_log import LOG_CONFIG

JUNIT_TO_JIRA_STATUS_MAP = {"passed": "Pass", "failed": "Fail", "skipped": "Not Executed", "untested": "Not Executed"}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('tmconnect')


def _clean_test_name(test_name):
    """Remove single and double quotes from the test name."""
    return test_name.replace('\'', "").replace('"', "")


def create_test_cycle(tm4j, name, artifact, env, reporter):
    """
    Create new test cycle in Jira and post test results from the provided artifact.
    Current artifacts.zip from Bamboo runs is supported.

    :param tm4j: Instance of TM4J class.
    :param name: Name of the new test cycle.
    :param artifact: Path to the artifact with test results.
    :param env: Environment where tests were executed (Must be present in the Jira project).
    :param reporter: Login of a person who executed the cycle (Must be a valid login).
    """

    logger.info(f"Creating test run {name}...")
    tm4j.post_new_testrun(name)

    with ZipFile(artifact, 'r') as artifacts_zip:

        tempdir = tempfile.mkdtemp()

        test_results = []
        for filename in artifacts_zip.namelist():
            if ".xml" in filename:
                logfile = "split_" + filename.split(".")[-2] + "_feature.log"
                test_results.append((filename, logfile))

        for test_result in test_results:
            junit, log = test_result
            logger.debug(f"Posting results from files {junit} {log} ...")
            with artifacts_zip.open(junit) as report:
                dom = parseString(report.read())
                test_name = dom.getElementsByTagName("testcase")[0].attributes['name'].value
                test_status = dom.getElementsByTagName("testcase")[0].attributes['status'].value
            test_name = _clean_test_name(test_name)
            test_status = JUNIT_TO_JIRA_STATUS_MAP[test_status]
            extracted_log = artifacts_zip.extract(log, tempdir)

            try:
                tm4j.find_testcase(test_name)  # !!!
                logger.info(f"Posting test run info for {tm4j.test_id} ...")
                tm4j.post_test_result(test_status, env, reporter)
                logger.info(f"Posting test log for {tm4j.test_id} ...")
                tm4j.attach_testcase_result_file(extracted_log)
            except (TM4JException, HTTPError) as exc:
                logger.exception(exc)
                continue

            logger.info(f"Test results for {tm4j.test_id} posted successfully.")


def main():
    from os import path
    tm4j = TM4J()
    artifact = path.join(path.abspath(path.dirname(__file__)), tm4j.config['JUNIT']['pathToArtifact'])
    test_cycle_name = tm4j.config['JUNIT']['testcycleName']
    env = tm4j.config['JUNIT']['env']
    reporter = tm4j.config['JUNIT']['reporter']

    create_test_cycle(tm4j, test_cycle_name, artifact, env, reporter)


if __name__ == '__main__':
    main()

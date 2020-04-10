"""
Library implements methods to work with csv-file of created test-cases,
update feature files with testcase keys
"""
import csv
from re import search
from libs.tm_log import get_logger
from libs.files import make_csv_path
from libs.config import log_config, gen_config
from libs.tags_parse_lib import clear_name, split_testcase_name_key

logger = get_logger(__name__)


def get_creates_tests_from_csv() -> list:
    """
    loads list of created tests from csv-file.
    Path to file is taken from config
    :return: list of lists
    """
    tc_creation_csv_log = make_csv_path(log_config, gen_config)
    with open(tc_creation_csv_log, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter='#')
        created_tests = list(reader)
    return created_tests


def get_scenario_name_position(line: str) -> int:
    """
    :return: position of scenario name in line or -1
    """
    new_line = line.strip()
    if new_line.startswith(('Scenario:', 'Scenario Outline:')):
        a = line.split(':')
        # len first part + 1 for : + len of leading spaces in second part
        return len(a[0]) + 1 + (len(a[1]) - len(a[1].lstrip(' ')))
    else:
        return -1


def get_tc_key_from_csv(test_name: str) -> str:
    """
    Looks for testname in csv-log of created testcases
    :param test_name: testname to look for in list of created
    :return: testcase key
    """
    created_tests = get_creates_tests_from_csv()
    test_name = r"" + test_name
    for test in created_tests:
        if bool(search(test[1], test_name)):
            logger.info(test[0])
            return test[0]
    raise LookupError(f'No key found in creation log for name {test_name}')


def update_feature_file_with_keys(key: str, name: str, feature_file_path: str):
    """
    Function updates scenario name in given feature file with testcase key
    :param key:
    :param name: scenario name to update
    :param feature_file_path: path to feature file
    :return:
    """
    logger.info(f'Trying to add keys: {locals()}')
    delimiter = gen_config['testCaseKeyDelimiter']
    new_lines = list()
    results = list()
    try:
        with open(feature_file_path, 'r') as file:
            for line in file:
                # doing all this stuff instead of replace because posted testcase names
                # are cleared with clear_name and in .feature file they are not, thus they might differ
                index = get_scenario_name_position(line)
                logger.debug(f'{line} - {index}')
                if index > 0:
                    cleared_name = clear_name(line[index:].strip())
                    n_key, n_name = split_testcase_name_key(cleared_name, gen_config['testCaseKeyDelimiter'])
                    # check if name starts with testCase key -- then no update required
                    if n_name == clear_name(name):
                        if n_key:
                            logger.info(f'Scenario \"{cleared_name}\" already has TM4J key and will be skipped')
                            new_lines.append(line)
                            continue
                        # add extra space after 'Scenario:' if missing
                        space = ' ' if len(line[:index]) == len(line[:index].rstrip(' ')) else ''
                        line = f'{line[:index]}{space}{key}{delimiter}{line[index:]}'
                        results.append(f'Key: {key} added to test {cleared_name}.')
                new_lines.append(line)
        with open(feature_file_path, 'w') as file:
            file.write("".join(new_lines))
        if len(results):
            logger.info(f'Update results: {" ".join(results)}')
        else:
            logger.info(f'No keys added -- no need.')
    except Exception as e:
        logger.error(f'{key, name, feature_file_path} -- {e}')


def main():
    """
    for every feature file in featuresFolderInLocalRepository updates scenario name
    by appending {key}{delimiter} to {name}
    """
    created_tests = get_creates_tests_from_csv()
    for test in created_tests:
        key, name, feature = test
        logger.info(key)
        try:
            update_feature_file_with_keys(key, name, feature_file_path=feature)
        except Exception as e:
            logger.error(f'{test} -- {e}')
    logger.info(f'Files update complete')


if __name__ == '__main__':
    main()

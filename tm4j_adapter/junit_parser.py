"""
Library implements parsing junit reports into TM4J testruns and testresults
"""

import argparse
from libs.config import read_config
from classes.JunitParser import JunitParser
from libs.files import FilesHandler
from libs.tm_log import get_logger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--tc_name", help="Test cycle name")
    parser.add_argument("-p", "--j_path", help="Path to json file or folder with files")
    parser.add_argument("-l", "--logs", help="Path to test execution logs")
    parser.add_argument("-c", "--config", help="Path to alternative config file")
    args = parser.parse_args()
    config_path = args.config if args.config else None
    config = read_config(config_path)
    logger = get_logger(__name__, config)
    try:
        junit_path = args.j_path if args.j_path else config['JUNIT']['junitPath']
        fh = FilesHandler(config, junit_path)
        testcycle_name = args.tc_name if args.tc_name else config['EXECUTION']['testcycleName']
        logs_path = args.logs if args.logs else \
            (config['JUNIT']['pathToLogs'] if config['JUNIT']['pathToLogs'] != '' else None)
        files_list = fh.get_list_of_files('xml')
        logger.info(f'Starting to parse json results. '
                    f'Config path: {config_path}  '
                    f'Tescycle name: {testcycle_name}  '
                    f'Logs path: {logs_path}   '
                    f'Files to proceed: {files_list}  ')
        j_parser = JunitParser(testcycle_name, config_path, logs_path)
        j_parser.read_files(files_list)
        j_parser.do_export_results()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()

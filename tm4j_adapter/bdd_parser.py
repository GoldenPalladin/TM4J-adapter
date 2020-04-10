"""
Library implements parsing BDD feature files into TM4J testcases
"""

import argparse
from classes.BddParser import BddParser
from libs.files import get_list_of_files, get_full_path, try_file_exists, find_file_in_list_by_name
from libs.test_log_parser import parse_log, remove_duplicates
from libs.config import read_config
from libs.tm_log import get_logger

logger = None


def get_list_of_feature_files_to_proceed(config, diff: str = None) -> list:
    """
    function returns list of feature files to proceed basing on config settings
    :param config:
    :param diff: abs path to alternate diff file
    :return: list of feature file paths either all or modified
    """
    logger.info(f'Getting list of feature files to proceed')
    bdd_config = config['BDD']
    updated_files_list = []
    use_relative_path = bool(config['GENERAL']['useRelativePath'])
    features_folder = get_full_path(bdd_config['localRepoRoot'], use_relative_path, bdd_config['featuresFolderInLocalRepository'])
    files_list = get_list_of_files(features_folder, '.feature', use_relative_path)
    if bdd_config['diffTestsUpdate'] == 'True':
        diff_file = diff if diff else get_full_path(bdd_config['localRepoRoot'], use_relative_path, bdd_config['diffFilePath'])
        diff_file = try_file_exists(diff_file, '', logger, use_relative_path, True)
        modified_files = parse_log(diff_file)
        modified_feature_files = list(filter(lambda x: '.feature' in x, modified_files))
        for modified_file in modified_feature_files:
            try:
                updated_files_list.append(find_file_in_list_by_name(modified_file, files_list, bdd_config, True))
            except FileNotFoundError:
                logger.error(f'File {modified_file} was not found locally, skipping...')
        logger.info(f'Diff_file {diff_file}. Diff feature files: {modified_feature_files}'
                    f'. Updated_files_list: {updated_files_list}')
        return remove_duplicates(updated_files_list)
    logger.info(f'Files_list: {files_list}.')
    return files_list


def main():
    global logger
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to alternative config file")
    parser.add_argument("-d", "--diff", help="Path to diff file to proceed")
    args = parser.parse_args()
    config_path = args.config if args.config else None
    diff_path = args.diff if args.diff else None
    config = read_config(config_path)
    logger = get_logger(__name__, config)
    try:
        files_list = get_list_of_feature_files_to_proceed(config=config, diff=diff_path)
        bdd_parser = BddParser(config_path)
        bdd_parser.read_files(files_list)
        bdd_parser.do_export_results()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()

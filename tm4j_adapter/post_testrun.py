
import argparse
from libs.config import read_config
from classes.RocsParser import RocsParser
from libs.bamboo import get_build_artifact
from libs.files import get_full_path
from libs.tm_log import get_logger


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to alternative config file")
    parser.add_argument("-k", "--trkey", help="TestCycle key to post results into")
    args = parser.parse_args()
    config_path = args.config if args.config else None
    config = read_config(config_path)
    key = args.trkey if args.trkey else None
    logger = get_logger(__name__, config)
    try:
        r_config = config['ROCS']
        testcycle_name = config['EXECUTION']['testcycleName']
        artifact_path = get_full_path(base_path=r_config['pathToArtifact'],
                                      use_relative_path=True)
        if r_config['getResultsFromBamboo'] == 'True':
            get_build_artifact(r_config['bambooBuildLink'], artifact_path)
        j_parser = RocsParser(artifact_path=artifact_path,
                              testcycle_name=testcycle_name,
                              testcycle_key=key,
                              config_path=config_path)
        j_parser.read_files()
        j_parser.do_export_results()
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()

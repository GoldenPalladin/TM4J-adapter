"""
Parsers classes
"""

from libs.tm_log import get_logger
from libs.config import read_config
from classes.TM4J import TM4J


class Parser:
    """
    base class to parse data and post into tm4j
    """
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = read_config(config_path)
        self.logger = get_logger(__name__, self.config)
        self.tm = TM4J(self.config_path)
        self.file = None
        self.file_contents = list()
        self.parse_results = list()
        self.export_results = {'Files read': 0, 'Results found': 0, 'Exported': 0, 'Failed': 0}

    def _read_single_file(self, file_path: str):
        """
        method to read contents of parsed file
        Should be overridden for specific parsers
        :param file_path: path to file
        """
        pass

    def read_files(self, files: list):
        """
        method to read contents of every file in list
        :param files: list of file paths to iterate
        """
        self.logger.info(f'Reading files to parse: {files}')
        if not files:
            raise FileNotFoundError('Cannot read files to parse. Files list is empty!')
        for file in files:
            self._read_single_file(file)
            self.export_results['Files read'] += 1
        self._parse_contents()

    def _parse_contents(self):
        """
        method to parse read contents into list of results
        Should be overridden for specific parsers
        """
        pass

    def _post_single_result(self, args: tuple):
        """
        method to post single result from list
        :param args: single result folded into tuple
        Should be overridden for specific parsers
        """
        pass

    def do_export_results(self, args: tuple = None):
        """
        method to post results from self.export_results
        :param args: some data relating to all results in list, like Executed by or Env
        """
        self.export_results['Results found'] = len(self.parse_results)
        self.logger.info(f'Exporting {len(self.parse_results)} results')
        for result in self.parse_results:
            new_args = (result,) + args if args else (result,)
            try:
                self._post_single_result(new_args)
                self.export_results['Exported'] += 1
            except Exception as e:
                self.export_results['Failed'] += 1
                self.logger.error(f"Parser -> Export results: Error exporting: {result}: {e}")
        self.logger.info(self.export_results)

    @staticmethod
    def match_execution_result(result: str) -> str:
        """
        function finds matching Jira formatted status in variants from dict
        :param result: string to search
        :return: matching name
        """
        import re
        statuses_map = {"Pass": ["passed", "pass"],
                        "Fail": ["is_failed", "fail", "failed"],
                        "Not Executed": ["skipped", "untested"],
                        "Blocked": ["blocked"]}
        for name, matches in statuses_map.items():
            for variant in matches:
                re_string = [r'']
                for word in variant.split(' '):
                    re_string.append(f'(?=.*\\b{word}\\b)')
                re_string.append('.*')
                if bool(re.search(''.join(re_string), result, re.IGNORECASE)):
                    return name
        raise LookupError(f'No match for {result} was found in execution statuses')

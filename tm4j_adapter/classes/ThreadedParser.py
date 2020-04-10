from classes.Parser import Parser
"""
Class using multithreading when exporting results
"""


class ThreadedParser(Parser):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.testcycle_key = None

    def do_export_results(self, args: tuple = None):
        import time
        from libs.multi_threading import run_threaded
        start = time.time()
        self.export_results['Results found'] = len(self.parse_results)
        self.logger.info(f'Exporting {len(self.parse_results)} results')
        failed_posts = run_threaded(self.parse_results, self._post_single_result, args)
        self.logger.info("Posting results took: {:.2f} seconds".format(time.time() - start))
        if failed_posts:
            self.logger.error(f'{" "*30} EXPORT HAS SOME ERRORS: {len(self.parse_results)} results were in report, '
                         f'but {len(failed_posts)} were not posted.')
            self.manage_unposted_results(failed_posts)
        else:
            self.logger.info('Execution results posted successfully.')
        self.export_results['Failed'] = len(failed_posts)
        self.export_results['Exported'] = len(self.parse_results) - len(failed_posts)
        self.logger.info(self.export_results)

    def manage_unposted_results(self, failed_posts: list):
        """
        function to manage unposted results -- export, save and so on.
        Should be overridden for specific parsers
        :param failed_posts:
        :return:
        """
        pass


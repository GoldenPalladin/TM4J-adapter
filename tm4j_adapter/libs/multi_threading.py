"""
Module implements multithreading execution os some functions and error handling
"""
from libs.config import gen_config
from concurrent.futures import ThreadPoolExecutor, as_completed
from libs.tm_log import get_logger

logger = get_logger(__name__)


def run_threaded(results_list: list, action: callable, args) -> list:
    threads_qty = int(gen_config['threadsQty'])
    retry_list = list()
    exceptions_list = list()
    future_to_post = {}
    counter = 0
    initial_list_size = len(results_list)
    with ThreadPoolExecutor(threads_qty) as executor:
        for result_to_post in results_list:
            values = add_tuple_to_item(result_to_post, args)
            future_to_post[executor.submit(action, values)] = result_to_post
            logger.debug(f'Added future to post {values}')
        for future in as_completed(future_to_post):
            if future.exception():
                retry_list.append(future_to_post[future])
                exceptions_list.append(future.exception())
            else:
                counter += 1
    logger.info(f'Posted {counter} results')
    if retry_list and (len(retry_list) < initial_list_size):
        logger.info(f'Retrying to post {len(retry_list)} results')
        run_threaded(retry_list, action, args)
    elif retry_list and (len(retry_list) == initial_list_size):
        logger.error(f'Exceptions do not converge. Exiting')
        logger.exception(f'Exceptions: {exceptions_list}')
        return retry_list
    return []


def add_tuple_to_item(item, tup: tuple) -> tuple:
    if not tup:
        return item
    elif isinstance(item, tuple):
        return item + tup
    elif isinstance(item, str):
        return (item,) + tup
    elif isinstance(item, list):
        return tuple(item + list(tup))
    else:
        raise TypeError(f'Unrecognized type of {item}')




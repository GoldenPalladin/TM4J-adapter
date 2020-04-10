"""
Library implements some filtering functions to work with scenario tags
"""
import re
import json
from classes.Exceptions import TM4JInvalidFolderName


def clear_name(name: str) -> str:
    """
    function do some manipulations to make name of some object to be acceptable for tm4j
    Otherwise error 500 is raised if name is larger than 255 chars or contains (double)quotes
    :param name:
    :return:
    """
    name = "".join(i for i in name if ord(i) < 128)  # get rid of non-unicode chars
    name = name.replace("'", "").replace('"', '').replace(u"\u2019", '').lstrip(':').lstrip(' ')
    name = name[:255] if len(name) > 255 else name
    return name


def check_folder_name(folder: str):
    if not (folder.replace('/', '').replace('_', '').replace('...', '').replace('-', '')).isalnum():
        raise TM4JInvalidFolderName(f"Folder '{folder}' must have alphanumeric name!")


def strip_none_values(obj):
    """constructs json from object without Null values"""
    if isinstance(obj, list):
        result = list()
        for item in obj:
            if isinstance(item, dict):
                item = {k: v for k, v in item.items() if v is not None}
            result.append(item)
    elif isinstance(obj, dict):
        try:
            name = clear_name(obj['name'])
            obj.update({'name': name})
        except KeyError:
            pass
        finally:
            result = {k: v for k, v in obj.items() if v is not None}
    else:
        result = obj
    return json.dumps(result)


def is_jira_issue(tag: str) -> bool:
    return bool(re.search(r'(?<!([^\s]))([A-Z,1-9]{1,10}-[1-9][0-9]{0,6})(?=(\s|$))', tag))


def is_tm4j_testcase_key(tag: str) -> bool:
    return bool(re.search(r'(?<!([^\s]))([A-Z,1-9]{1,10}-T[0-9]{0,6})(?=(\s|$))', tag))


def is_priority(tag: str) -> bool:
    return bool(re.search(r'P[0-3]', tag))


def append_filtered_list_to_dict(source: list, filter_function: callable, destination: dict, key_name: str) -> dict:
    """
    :param source: list to filter
    :param filter_function:
    :param destination: dict to append results
    :param key_name: key to append results
    :return: updated dict
    """
    value = list(filter(filter_function, source))
    if value:
        destination.update({key_name: value})
    return destination


def parse_scenario_tags(tags: list) -> dict:
    """tags split into jira, priority or tags list"""
    result = dict()
    append_filtered_list_to_dict(tags, is_jira_issue, result, 'issueLinks')
    append_filtered_list_to_dict(tags, is_priority, result, 'priority')
    append_filtered_list_to_dict(tags, lambda tag: not(is_jira_issue(tag) or is_priority(tag)), result, 'labels')
    priority_map = {'P2': 'Low', 'P1': 'Normal', 'P0': 'High'}
    if 'priority' in result:
        result.update(priority=priority_map.get(min(result.get('priority'))))
    return result


def split_list(source: list, parts: int) -> iter:
    """
    splits a list into parts
    :param source: list to split
    :param parts: number of parts
    :return:
    """
    k, m = divmod(len(source), parts)
    return (source[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(parts))


def split_testcase_name_key(name_to_split: str, delimiter: str) -> tuple:
    key = None
    splitted_name = name_to_split.split(delimiter)
    # check if name starts with testCase key -- then no update required
    if is_tm4j_testcase_key(splitted_name[0]):
        key = splitted_name[0]
        name = splitted_name[1]
    else:
        name = name_to_split
    return key, name


def choose(value, true_result, false_result=None):
    """Some logic to shortify code"""
    if value:
        return true_result
    elif false_result:
        return false_result
    else:
        return ''


def validate_script_results_json(script: list) -> list:
    """filter unwanted keys in script results"""
    keys = ['index', 'status', 'comment']
    result = []
    for step in script:
        result.append(dict([(i, step[i]) for i in step if i in set(keys)]))
    return result


def is_true(var: str) -> bool:
    """
    function to make string comparing of config items
    :param var:
    :return:
    """
    try:
        return var.lower() == 'true'
    except Exception:
        return False


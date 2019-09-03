"""
Library parses log files by test name and returns unduplicated artifacts
"""


def parse_test_log(file: str) -> list:
    with open(file, 'r') as content:
        test_logs = _split_list(content.read().splitlines())
    return test_logs


def _split_list(input_lines: list) -> dict:
    """
    Function parses logs into dict like {testName:[some, lines, between, test, names]
    :param input_lines: list of test logs refined from timestamps
    :return: dict
    """
    result = {' ': []}
    current_test_name = ' '
    for line in input_lines:
        last_words = line.split(':')[-1]
        if _is_test_name(last_words):
            current_test_name = last_words.strip()
            result.update({current_test_name: []})
        else:
            result[current_test_name].append(last_words)
    return {k: _remove_duplicates(v) for k, v in result.items() if k != ' '}


def _remove_duplicates(x: list) -> list:
    return list(dict.fromkeys(x))


def _is_test_name(text: str) -> bool:
    import re
    """function checks if text is in 'testXxxXxx format"""
    return bool(re.search(r"test[A-Za-z]+", text))

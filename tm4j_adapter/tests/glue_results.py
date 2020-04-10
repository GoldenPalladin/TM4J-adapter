from classes.RocsParser import RocsParser
from libs.files import get_full_path
from libs.tags_parse_lib import split_testcase_name_key
from tests.config import rocs_config

def main():
    artifact = "C:\\Users\\pyakovlev\\Downloads\\case_assesment.zip"
    rocs = RocsParser(artifact, 'test', rocs_config['configPath'])
    rocs.read_files()
    tc_key = 'CST-T1712'
    results = rocs.parse_results
    filtered = [(x[0], x[3]) for x in results if tc_key == split_testcase_name_key(x[0], '_')[0]]
    print(filtered)


if __name__ == '__main__':
    main()



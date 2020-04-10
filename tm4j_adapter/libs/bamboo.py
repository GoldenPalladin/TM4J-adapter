import logging.config
from urllib.request import urlopen
from urllib.error import HTTPError
from libs.tm_log import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('postTestrun')


def get_build_artifact(build_url: str, save_as: str):
    """
    download bamboo artifact to specified path
    :param build_url: bamboo build url
    :param save_as: name to save file as
    :return: path to downloaded artifact
    """
    download_url = f'{build_url}/artifact/GR/artifacts/artifacts.zip'
    reserve_download_url = f'{build_url}/artifact/GR/artifacts.zip/artifacts.zip'
    logger.info(f'Starting download artifact from {download_url}')
    try:
        filedata = urlopen(download_url)
    except HTTPError as e:
        logger.info(f'Download failed')
        if e.code == 404:
            logger.info(f'Starting download artifact from {reserve_download_url}')
            filedata = urlopen(reserve_download_url)
        else:
            raise e
    data_to_save = filedata.read()
    with open(save_as, 'wb') as f:
        f.write(data_to_save)
    logger.info(f'Artifact downloaded and saved as {save_as}')



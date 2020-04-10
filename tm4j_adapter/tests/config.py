import configparser

config_path = 'config.ini'
c_config = configparser.ConfigParser()
c_config.read(config_path)
bdd_config = c_config['BDD']
rocs_config = c_config['Rocs']
tm_config = c_config['tm']


import configparser
import os
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Config:
    config_file = '/Users/kozlovalex/Documents/GitHub/python_web_12.V1/src/conf/config.ini'

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    try:
        DBName = config.get('DB', 'DBName')
        PASS = config.get('DB', 'PASS')
        DB_NAME = config.get('DB', 'DB_NAME')
        DOMAIN = config.get('DB', 'DOMAIN')
        PORT = config.get('DB', 'PORT')

    except configparser.NoSectionError as e:
        raise ValueError(f"Missing section in configuration file: {e.section}")

    DB_URL = f"postgresql+asyncpg://{DBName}:{PASS}@{DOMAIN}:{PORT}/{DB_NAME}"


config = Config

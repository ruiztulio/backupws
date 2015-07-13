#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This script creates development-test OpenERP databases from
backup files
"""

import os
import logging
import argparse

from lib import utils
from deactivate_ws import deactivate

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--backup-file", help="Path of backup file",
                    required=True)
parser.add_argument("--log-level", help="Level of logger. INFO as default",
                    default="info")
parser.add_argument("--logfile", help="File where log will be saved",
                    default=None)
parser.add_argument("--config-file", help="Json file with possible config",
                    default="config-bd.json")
parser.add_argument("--config", help="Database config", required=True)
parser.add_argument("--temp-dir", help="Temp working dir", default="/tmp")

args = parser.parse_args()
level = getattr(logging, args.log_level.upper(), None)
logging.basicConfig(level=level,
                    filename=args.logfile,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("testbd_creator")

db_file = args.backup_file
json_file = args.config_file
config = args.config
tmp = args.temp_dir


def restore_database(db_name, db_config, dump_dest, port):
    """This function restores and deactivates a database from a dump

    :param db_name: Database name
    :param db_config: Dict with database configuration
    :param dump_dest: Dump to be used
    :param port: Config Port from db_config used for connection
    :return: 1 if connection failed, 2 if database exists, db_name if
            succesfull
    """
    if not utils.test_connection(db_name, db_config['host'],
                                 db_config['port'][port], db_config['user'],
                                 db_config['pswd'], only_connection=True):
        return 1
    if utils.database_exists(db_name, db_config['host'],
                             db_config['port'][port]):
        logger.error("Database %s already exists, aborting program", db_name)
        return 2
    try:
        logger.info("Restoring database...")
        utils.restore_database(dump_dest, db_name, db_config['superpswd'],
                               db_config['host'], db_config['port'][port])
        logger.debug("Database restored")
        logger.info("Deactivating database...")
        deactivate(db_name, db_config['user'], db_config['pswd'],
                   db_config['host'], db_config['port'][port])
        logger.debug("Database deactivated")
    except Exception as e:
        logger.error(e)
        return 1
    return db_name

def create_test_db(prefix, db_file, db_config, temp_dir):
    """
    This function creates a database from backup file with determined config

    :param prefix: Prefix for database name
    :param db_file: Backup file for database
    :param db_config: Dict with database configuration
    :param temp_dir: Temporary directory for dump
    :return: Database name if succesfull, 1 otherwise
    """
    str_list = os.path.basename(db_file).split(".")[0].split("-")
    db_name = prefix + "_" + str_list[len(str_list) - 1].split("_", 1)[1]
    logger.debug("Database name: %s", db_name)
    dump_dest = utils.decompress_files(db_file, temp_dir)
    result = restore_database(db_name, db_config, dump_dest, "xmlrpc")
    if result == 1:
        result = restore_database(db_name, db_config, dump_dest, "opt")
    utils.clean_files([dump_dest])
    return result


if __name__ == '__main__':
    logger.info("Creating %s database from %s backup", config, db_file)
    db_config = utils.load_json(json_file)
    db = create_test_db(config, db_file, db_config[config], tmp)
    if db != 1:
        logger.info("Database %s created", db)

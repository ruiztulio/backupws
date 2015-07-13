#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This script creates development-test OpenERP databases from
backup files
"""

import os
import datetime
import logging
import argparse

from lib import utils
from deactivate_ws import deactivate

parser = argparse.ArgumentParser()
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("-f", "--backup-file", help="Path of backup file")
action.add_argument("-p", "--backup-path",
                    help="Path of backup dir. Most recent backup will be restored")
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
path = args.backup_path
json_file = args.config_file
config = args.config
tmp = args.temp_dir


def get_date(db_file):
    """This function takes the creation date of a backup file, from its name

    :param db_file: Backup file
    :return: Backup date if succesfull. '0001-01-01 00:00:00' otherwise
    """
    date_str = os.path.basename(db_file).split(".")[0]
    str_list = date_str.split("-")
    str_list = str_list[len(str_list) - 1].split("_")
    date_str = str_list[len(str_list) - 2]
    time_str = str_list[len(str_list) - 1]
    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:])
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:])
        file_date = datetime.datetime(year=year, month=month, day=day,
                                      hour=hour, minute=minute, second=second)
    except Exception as e:
        file_date = datetime.datetime(year=datetime.MINYEAR, month=1, day=1,
                                      hour=0, minute=0, second=0)
        logger.error("File: %s - %s", os.path.basename(db_file), e)
    return file_date


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


def select_file(path):
    """This function selects the most recent backup file in 'path' dir

    :param path: Backup path directory
    :return: Most recent db_file
    """
    logger.debug("Selecting backup file to be restored")
    db_select = os.listdir(path)[0]
    for dfile in os.listdir(path):
        if get_date(dfile) > get_date(db_select):
            db_select = dfile
    logger.info("File %s selected", os.path.basename(db_select))
    return db_select

if __name__ == '__main__':
    if not db_file:
        db_file = select_file(path)
    logger.info("Creating %s database from %s backup", config, db_file)
    db_config = utils.load_json(json_file)
    db = create_test_db(config, db_file, db_config[config], tmp)
    if db != 1:
        logger.info("Database %s created", db)

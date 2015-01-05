#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to resore Odoo DB dumps using Oerplib and
works with backup_db_ws
"""
import logging
import argparse
import sys
from lib import utils

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')




def main(main_args):
    """ Main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Database name", default=False)
    parser.add_argument("-f", "--file", help="Backup name to resore", default=False, required=True)
    parser.add_argument("-t", "--temp_dir", help="Temp working dir", default="/tmp")
    parser.add_argument("-H", "--host", help="Host running Odoo", default="localhost")
    parser.add_argument("-p", "--port", help="Odoo xmlrpc port", default=8069)
    parser.add_argument("-u", "--user", help="Odoo super user", default="admin")
    parser.add_argument("-w", "--password", help="Odoo super user pass", default="admin")

    args = parser.parse_args(main_args)
    if not utils.test_connection(args.db, args.host, args.port, args.user, args.password):
        return 1
    if utils.database_exists(args.db, args.host, args.port):
        logger.error("Database %s already exits, aborting program", args.db)
        return 1
    dump_dest = utils.decompress_files(args.file, args.temp_dir)
    utils.restore_database(dump_dest, args.db, args.password, args.host, args.port)
    utils.clean_files([dump_dest])
    return 0

if __name__ == '__main__':
    logger.info("Starting restore process")
    sys.exit(main(sys.argv[1:]))
    logger.info("Resore process has finished")

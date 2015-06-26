#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to make Odoo DB dumps using Oerplib
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
    parser.add_argument("dbs", help="Comma separated dabases names to backup",
                        default=False)
    parser.add_argument("-t", "--temp_dir", help="Temp working dir",
                        default="/tmp")
    parser.add_argument("-d", "--backup_dir", help="Where to store backups",
                        default=".")
    parser.add_argument("-r", "--reason",
                        help="Reason why are  making this backup",
                        default=False)
    parser.add_argument("-H", "--host", help="Host running Odoo",
                        default="localhost")
    parser.add_argument("-p", "--port", help="Odoo xmlrpc port",
                        default=8069)
    parser.add_argument("-u", "--user",
                        help="Odoo super user", default="admin")
    parser.add_argument("-w", "--password", help="Odoo super user pass",
                        default="admin")
    parser.add_argument("-k", "--keep_latest", help="Keep the lastest generated backup without compression in the specified folder",
                        default=False)

    args = parser.parse_args(main_args)
    db_list = [x.strip() for x in args.dbs.split(',')]
    if not utils.test_connection(db_list[0], args.host, args.port,
                                 args.user, args.password,
                                 only_connection=True):
        return 1
    utils.backup_databases(db_list, args.backup_dir, args.user,
                           args.password, args.host, args.port,
                           args.reason, args.temp_dir,
                           keep_path=args.keep_latest)
    return 0

if __name__ == '__main__':
    logger.info("Starting backup process")
    res = main(sys.argv[1:])
    if res == 0:
        logger.info("Backup process has finished")
    sys.exit(res)

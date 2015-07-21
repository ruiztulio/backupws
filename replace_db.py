#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to restore Odoo DB dumps using config gotten from docker env vars
or directly from config file bus replacing it (and the filestore
"""
import logging
import configargparse
import sys
from lib import utils
from tempfile import mkdtemp, gettempdir

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')

def main(main_args):
    """ Main function
    """
    parser = configargparse.ArgParser()
    parser.add("-d", "--database", help="Database name to retore the backup",
               default=False, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add('-o', '--odoo_configfile',
               help='Config file path (mutually exclusive with -f option)',
               default=False)
    action.add('-f', '--from_docker',
               help=('Docker container which has the configuration',
                     ' (mutually exclusive with -o option)'),
               default=False)
    parser.add('-c', '--config_file', 
               help='Config file path', is_config_file=True)
    parser.add("-t", "--temp_dir", help="Temp working dir",
               default=gettempdir())
    parser.add("-b", "--backup", help="Backup file to be restored",
               default=False, required=True)

    args = parser.parse_args(main_args)
    if (args.from_docker and args.odoo_configfile) or \
        (not args.from_docker and not args.odoo_configfile):
        print "You must specify one of two options -o or -f\n\n"
        print(parser.format_help())
        return 1
    if args.from_docker:
        odoo_cfg = utils.parse_docker_config(args.from_docker)
    elif args.odoo_configfile:
        odoo_cfg = utils.pase_odoo_configfile(args.odoo_configfile)
    odoo_cfg.update({'database': args.database})
    working_dir = mkdtemp(prefix='vxRestore_', dir=args.temp_dir)
    if utils.dropdb_direct(odoo_cfg):
        utils.remove_attachments(odoo_cfg)
        utils.restore_direct(args.backup, odoo_cfg, working_dir)

if __name__ == '__main__':
    logger.info("Starting backup process")
    main(sys.argv[1:])
    logger.info("Backup process has finished")

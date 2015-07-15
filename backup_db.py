#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to make Odoo DB dumps using Oerplib
"""
import logging
import configargparse
import sys
from lib import utils
import os
from tempfile import gettempdir


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')

def main(main_args):
    """ Main function
    """
    parser = configargparse.ArgParser()
    parser.add("-d", "--database", help="Database name to backup",
        default=False)
    parser.add('-o', '--odoo_configfile', 
        help='Config file path (mutually exclusive with -f option)', default=False)
    parser.add('-f', '--from_docker', 
        help='Docker container which has the configuration (mutually exclusive with -o option)', default=False)
    parser.add('-c', '--config_file', 
        help='Config file path', is_config_file=True)
    parser.add("-t", "--temp_dir", help="Temp working dir",
        default=gettempdir())
    parser.add("-b", "--backup_dir", help="Where to store backups",
        default=".")
    parser.add("-r", "--reason",
        help="Reason why are  making this backup",
        default=False)

    args = parser.parse_args(main_args)
    if (args.from_docker and args.odoo_configfile) or \
        (not args.from_docker and not args.odoo_configfile):
        print "You must specify one of two options -o or -f\n\n"
        print(parser.format_help())
        return 1
    if args.odoo_configfile:
        odoo_cfg = utils.pase_odoo_configfile(args.odoo_configfile)
    elif args.from_docker:
        odoo_cfg =  utils.parse_docker_config(args.from_docker)
    odoo_cfg.update({'database': args.database})
    dump_name = utils.pgdump_database(args.temp_dir, odoo_cfg)
    bkp_name = utils.generate_backup_name(args.database, args.reason)
    files2backup = [dump_name]
    if odoo_cfg.get('data_dir'):
        attachments_folder = os.path.join(odoo_cfg.get('data_dir'), 'filestore', odoo_cfg.get('database'))
        if os.path.exists(attachments_folder):
            logger.info('Attachements folder "%s"', attachments_folder)
            files2backup.append((attachments_folder, 'filestore'))
        else:
            logger.warn('Folder "%s" does not exists, attachements are not being added to the backup', attachments_folder)
    else:
        logger.info('There is not attachements folder to backup')
    utils.compress_files(bkp_name, files2backup)
    print dump_name
    #utils.pase_odoo_configfile('config.conf')


if __name__ == '__main__':
    logger.info("Starting backup process")
    main(sys.argv[1:])
    logger.info("Backup process has finished")

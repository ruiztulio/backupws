#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to make Odoo DB dumps using Oerplib
"""
import oerplib
import shutil
import datetime                                                                                                                                                                           
import tarfile
import os
import bz2
import logging
import argparse

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')

parser = argparse.ArgumentParser()
parser.add_argument("dbs", help="Comma separated dabases names to backup", default=False)
parser.add_argument("-t", "--temp_dir", help="Temp working dir", default="/tmp")
parser.add_argument("-d", "--backup_dir", help="Where to store backups", default=".")
parser.add_argument("-r", "--reason", help="Reason why are toy making this backup", default=False)
parser.add_argument("-H", "--host", help="Host running Odoo", default="localhost")
parser.add_argument("-p", "--port", help="Odoo xmlrpc port", default=8069)
parser.add_argument("-u", "--user", help="Odoo super user", default="admin")
parser.add_argument("-w", "--password", help="Odoo super user pass", default="admin")


args = parser.parse_args()
DATABASES = [x.strip() for x in args.dbs.split(',')]
DEST_FOLDER = args.temp_dir
BACKUP_DIR= args.backup_dir
HOST = args.host
PORT = args.port
USER = args.user
PASSWORD = args.password

FILES = []

def clean_files(files):
    """
    Remove unnecesary and temporary files
    """
    for fname in files:
        os.remove(fname)

def compress_files(name, files):
    """
    Compress a file, set of files or a folder in tar.bz2 format
    """
    logger.debug("Generating compressed file: %s", name)
    bz2_file = bz2.BZ2File(os.path.join(BACKUP_DIR, '%s.tar.bz2'%name), mode='w', compresslevel=9)
    with tarfile.open(mode='w', fileobj=bz2_file) as tar_bz2_file:
        for fname in files:
            tar_bz2_file.add(fname, os.path.join(name, os.path.basename(fname)))
    bz2_file.close()

def dump_database(dest_folder, database_name, super_user_pass, host, port):
    """
    Dump database using Oerplib in Base64 format
    """
    logger.debug("Dumping database %s into %s folder", database_name, dest_folder)
    dump_name = os.path.join(DEST_FOLDER, 'database_dump.b64')
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=3000)
    binary_data = oerp.db.dump(super_user_pass, database_name)
    with open(dump_name, "w") as fout:
        fout.write(binary_data)
    return dump_name

def backup_databases(databases_list, reason=False):
    """
    Receive a list of databases and backup up them all
    """
    for database in databases_list:
        if reason:
            file_name = '%s_%s_%s'% \
                        (database, reason, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        else:
            file_name = '%s_%s'%(database, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        logger.info("Dumping database")
        dbase = dump_database(DEST_FOLDER, database, USER, HOST, PORT)
        FILES.append(os.path.join(DEST_FOLDER, dbase))
        logger.info("Compressing dump %s", dbase)
        compress_files(file_name, FILES)
    clean_files(FILES)

        #decompress_files(file_name+'.tar.bz2', '.')
if __name__ == '__main__':
    logger.info("Starting backup process")
    backup_databases(DATABASES, args.reason)
    logger.info("Backup process has finished")

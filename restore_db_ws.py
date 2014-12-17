#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script is a PoC to resore Odoo DB dumps using Oerplib and
works with backup_db_ws
"""
import oerplib
import shutil
import tarfile
import os
import bz2
import logging
import argparse

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')

parser = argparse.ArgumentParser()
parser.add_argument("db", help="Database name", default=False)
parser.add_argument("-f", "--file", help="Backup name to resore", default=False, required=True)
parser.add_argument("-t", "--temp_dir", help="Temp working dir", default="/tmp")
parser.add_argument("-H", "--host", help="Host running Odoo", default="localhost")
parser.add_argument("-p", "--port", help="Odoo xmlrpc port", default=8069)
parser.add_argument("-r", "--user", help="Odoo super user", default="admin")
parser.add_argument("-w", "--password", help="Odoo super user pass", default="admin")


args = parser.parse_args()
DATABASE = args.db
DEST_FOLDER = args.temp_dir
BACKUP_DIR= args.backup_dir
HOST = args.host
PORT = args.port
USER = args.user
PASSWORD = args.password

def clean_files(files):
    """
    Remove unnecesary and temporary files
    """
    for fname in files:
        if os.path.isfile(fname):
            os.remove(fname)
        elif os.path.isdir(fname):
            shutil.rmtree(fname)


def decompress_files(name, dest_folder):
    """
    Decompress a file, set of files or a folder in tar.bz2 format
    """
    logger.debug("Decompressing file: %s", name)
    bz2_file = bz2.BZ2File(os.path.join(BACKUP_DIR, name), mode='r')
    tar = tarfile.open(mode='r', fileobj=bz2_file)
    tar.extractall(dest_folder)
    name_list = tar.getmembers()
    tar.close()
    bz2_file.close()
    for name in name_list:
        if os.path.basename(name.name) == 'database_dump.b64':
            base_folder = os.path.basename(name.name)

    logger.debug("Destination folder: %s", dest_folder)
    logger.debug("Bakcup folder: %s", base_folder)
    if name.endswith('tar.bz2') or name.endswith('tar.gz'):
        fname = os.path.basename(name)
        dest_folder = os.path.join(dest_folder, base_folder)
    logger.debug("Destination folder: %s", dest_folder)
    return dest_folder

def restore_database(dest_folder, database_name, super_user_pass, host, port):
    """
    Restore database using Oerplib in Base64 format
    """
    logger.info("Restoring database %s", database_name)
    dump_name = os.path.join(dest_folder, 'database_dump.b64')
    logger.debug("Restore dump - reading file %s", dump_name)
    with open(dump_name, "r") as fin:
        b64_str = fin.read()
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=3000)
    oerp.db.restore(super_user_pass, database_name, b64_str)

if __name__ == '__main__':
    logger.info("Starting restore process")
    dump_dest = decompress_files(args.file, DEST_FOLDER)
    restore_database(dump_dest, DATABASE, 'admin', HOST, PORT)
    clean_files([dump_dest])
    logger.info("Resore process has finished")

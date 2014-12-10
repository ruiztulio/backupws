#!/usr/bin/python
# -*- coding: utf-8 -*-

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
parser.add_argument("db", help="Database name", default=False)
parser.add_argument("-f", "--file", help="Backup name to resore", default=False, required=True)
parser.add_argument("-t", "--temp_dir", help="", default="/tmp")
parser.add_argument("-d", "--backup_dir", help="/var/lib/postgresql/db_backup", default=".")
parser.add_argument("-H", "--host", help="", default="localhost")
parser.add_argument("-p", "--port", help="", default=8069)

args = parser.parse_args()
DATABASE = args.db
DEST_FOLDER = args.temp_dir
BACKUP_DIR= args.backup_dir
HOST = args.host
PORT = args.port
USER = 'admin'
PASSWORD = 'admin'

def clean_files(files):
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
        elif os.path.isdir(f):
            shutil.rmtree(f)


def decompress_files(name, dest_folder):
    logger.debug("Decompressing file: %s", name)
    bz2_file = bz2.BZ2File(os.path.join(BACKUP_DIR, name), mode='r')
    tar = tarfile.open(mode='r', fileobj=bz2_file)
    tar.extractall(dest_folder)
    tar.close()
    bz2_file.close()
    logger.debug("Destination folder: %s", dest_folder)
    if name.endswith('tar.bz2') or name.endswith('tar.gz'):
        dest_folder =  os.path.join(dest_folder, name.split('.')[0])
    logger.debug("Destination folder: %s", dest_folder)
    return dest_folder

def restore_database(dest_folder, database_name, super_user_pass, host, port):
    logger.info("Restoring database %s", database_name)
    dump_name = os.path.join(dest_folder, 'database_dump.b64')
    logger.debug("Restore dump - reading file %s", dump_name)
    fin = open(dump_name, "r")
    b64_str = fin.read()
    fin.close()
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=3000)
    oerp.db.restore(super_user_pass, database_name, b64_str)

if __name__ == '__main__':
    logger.info("Starting restore process")
    dump_dest = decompress_files(args.file, DEST_FOLDER)
    restore_database(dump_dest, DATABASE, 'admin', HOST, PORT)
    clean_files([dump_dest])
    logger.info("Resore process has finished")
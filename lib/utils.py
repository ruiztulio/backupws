import shutil
import datetime
import tarfile
import os
import bz2
import logging
import oerplib


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('utils')

def clean_files(files):
    """ Remove unnecesary and temporary files

    Args:
        files (list): A list of absolute or relatove paths thar will be erased
    """
    for fname in files:
        if os.path.isfile(fname):
            os.remove(fname)
        elif os.path.isdir(fname):
            shutil.rmtree(fname)

def compress_files(name, files, dest_folder=None):
    """ Compress a file, set of files or a folder in tar.bz2 format

    Args:
        name (str): Desired file name w/o extenssion
        files (list): A list with the absolute o relative path to the files
                      that will be added to the compressed file
        dest_folder (str): The folder where will be stored the compressed file
    """
    if not dest_folder:
        dest_folder = '.'
    logger.debug("Generating compressed file: %s in %s folder", name, dest_folder)
    full_name = os.path.join(dest_folder, '%s.tar.bz2'%name)
    bz2_file = bz2.BZ2File(full_name, mode='w', compresslevel=9)
    with tarfile.open(mode='w', fileobj=bz2_file) as tar_bz2_file:
        for fname in files:
            tar_bz2_file.add(fname, os.path.join(name, os.path.basename(fname)))
    bz2_file.close()
    return full_name

def decompress_files(name, dest_folder):
    """ Decompress a file, set of files or a folder compressed in tar.bz2 format

    Args:
        name (str): Compressed file name
        dest_folder (str): Folder where the compressed file will be stored
    Returns:
        The absolute path to decompressed folder or file 
    """
    logger.debug("Decompressing file: %s", name)
    bz2_file = bz2.BZ2File(name, mode='r')
    tar = tarfile.open(mode='r', fileobj=bz2_file)
    tar.extractall(dest_folder)
    name_list = tar.getmembers()
    tar.close()
    bz2_file.close()
    for fname in name_list:
        if os.path.basename(fname.name) == 'database_dump.b64':
            base_folder = os.path.dirname(fname.name)

    logger.debug("Destination folder: %s", dest_folder)
    logger.debug("Bakcup folder: %s", base_folder)
    if name.endswith('tar.bz2') or name.endswith('tar.gz'):
        fname = os.path.basename(name)
        dest_folder = os.path.join(dest_folder, base_folder)
    logger.debug("Destination folder: %s", dest_folder)
    return dest_folder

def dump_database(dest_folder, database_name, super_user_pass, host, port):
    """ Dumps database using Oerplib in Base64 format

    Args:
        dest_folder (str): Folder where the function will save the dump
        database_name (str): Database name that will be dumped
        super_user_pass (str): Super user password to be used to connect with odoo instance
        host (str): Host name or IP address to connect
        port (int): Port number which Odoo instance is listening to
    Returns:
        The full dump path and name with .b64 extension
    """
    logger.debug("Dumping database %s into %s folder", database_name, dest_folder)
    dump_name = os.path.join(dest_folder, 'database_dump.b64')
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=3000)
    binary_data = oerp.db.dump(super_user_pass, database_name)
    with open(dump_name, "w") as fout:
        fout.write(binary_data)
    return dump_name

def backup_database(database_name, dest_folder, user, password, host, port, reason=False, tmp_dir=False):
    """ Receive database name and back it up

    Args:
        database_name (str): The database name
        dest_folder (str): Folder where the backup will be stored
        user (str): Super user login in the instance
        password (str): Super user password
        host (str): Hostname or ip where the Odoo instance is running
        port (int): Port number where the instance is llinstening
        reason (str): Optional parameter that is used in case 
                      there is a particular reason for the backup
        tmp_dir (str): Optional parameter to store the temporary working dir, default is /tmp

    Returns:
        Full path to the backup
    """
    files = []
    if reason:
        file_name = '%s_%s_%s'% \
                    (database_name, reason, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    else:
        file_name = '%s_%s'%(database_name, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    logger.info("Dumping database")
    dbase = dump_database(tmp_dir, database_name, password, host, port)
    files.append(os.path.join(tmp_dir, dbase))
    logger.info("Compressing dump %s", dbase)
    full_name = compress_files(file_name, files, dest_folder)
    clean_files(files)
    return full_name

def backup_databases(databases_list, dest_folder,
                     user, password, host, port, reason=False, tmp_dir=False):
    """ Receive a list of databases and backup up them all

    Args:
        databases_list (list): The database list name that will be 
    """
    for database in databases_list:
        logger.info("Dumping database")
        backup_database(database, dest_folder, user, password, host, port, reason, tmp_dir)


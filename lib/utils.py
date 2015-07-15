import shutil
import datetime
import tarfile
import os
import bz2
import logging
import oerplib
import socket
import json
import ConfigParser
import subprocess
import spur
import shlex
import collections
from docker import Client
import docker.errors

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('utils')


def save_json(info, filename):
    """Save info into Json file.

    Args:
        info: Object to be saved
        filename: Name of Json file

    Returns:
        Absolute path of Json file
    """
    logger.debug("Opening file %s", filename)
    try:
        with open(filename, 'w') as fout:
            json.dump(info, fout, sort_keys=True, indent=4, ensure_ascii=False,
                      separators=(',', ':'))
            if not os.path.isabs(filename):
                filename = os.path.abspath(filename)
            logger.debug("File saved")
    except Exception as e:
        logger.error(e)
    return filename


def load_json(filename):
    """ Load info from Json file

    Args:
        filename: Name of Json file

    Returns: Object loaded
    """
    logger.debug("Opening file %s", filename)
    with open(filename, "r") as f:
        info = json.load(f)
        logger.debug("File loaded")
        return info


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


def simplify_path(b_info):
    """This function deletes all common directories in branches' path

    Args:
        b_info: List of dictionaries with branches' info

    Returns:
        List of dictionaries with branches' info
    """
    logger.debug("Deleting all common branches' path")
    repeated = True
    while repeated:
        piece_path = []
        for branch in b_info:
            piece_path.append(branch['path'].split('/', 1)[0])
        word = piece_path[0]
        repeated = True
        for each in piece_path:
            if each != word:
                repeated = False
        if repeated:
            for branch in b_info:
                branch.update({'path': branch['path'].split('/', 1)[1]})
    logger.debug("Common paths deleted")
    return b_info


def name_from_url(url):
    """Takes name of a GIT repo from origin url

    Args:
        url (str): Url of GIT repo

    Returns:
        Repo's name
    """
    name = url
    while '/' in name:
        name = name.split('/', 1)[1]
    name = name.split('.', 1)[0]
    return name


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
    full_name = os.path.join(dest_folder, '%s.tar.bz2' % name)
    bz2_file = bz2.BZ2File(full_name, mode='w', compresslevel=9)
    with tarfile.open(mode='w', fileobj=bz2_file) as tar_bz2_file:
        for fname in files:
            if hasattr(fname, '__iter__'):
                tar_bz2_file.add(fname[0], os.path.join(name, fname[1]))
            else:
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
    base_folder = None
    for fname in name_list:
        if os.path.basename(fname.name) == 'database_dump.b64' or \
            os.path.basename(fname.name) == 'database_dump.sql':
            base_folder = os.path.dirname(fname.name)
            break

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
        super_user_pass (str): Super user password to be used 
                               to connect with odoo instance
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

def generate_backup_name(database_name, reason=False):
    """Generates the backup name accordint to the following standar:
       database_name_reason_YYYYmmdd_HHMMSS

       If reason is none:
       database_name_YYYYmmdd_HHMMSS
    """
    if reason:
        res = '%s_%s_%s'% \
                    (database_name, reason, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    else:
        res = '%s_%s'%(database_name, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    return res

def backup_database_ws(database_name, dest_folder, user, password, host, port, reason=False, tmp_dir=False):
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
    file_name = generate_backup_name(database_name, reason)
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
        backup_database_ws(database, dest_folder, user, password, host, port,
                        reason, tmp_dir)


def restore_database(dest_folder, database_name, super_user_pass, host, port):
    """ Restore database using Oerplib in Base64 format

    Args:
        dest_folder (str): Folder where the backup is stored
        database_name (str): The database name that will be created to restore the dump
        super_user_pass (str): Super user password of the instance
        host (str): Hostname or ip where the Odoo instance is running
        port (int): Port number where the instance is llinstening
    """
    logger.info("Restoring database %s", database_name)
    dump_name = os.path.join(dest_folder, 'database_dump.b64')
    logger.debug("Restore dump - reading file %s", dump_name)
    with open(dump_name, "r") as fin:
        b64_str = fin.read()
        logger.debug("File loaded")
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=3000)
    logger.debug("Connection to OERP established, restoring...")
    oerp.db.restore(super_user_pass, database_name, b64_str)


def database_exists(database_name, host, port=8069, timeout=3000):
    """ Check if a given database exists

    Args:
        database_name (str): Database name to be checked
        host (str): Hostname or ip where the Odoo instance is running
        port (int): Integer value specifying the port where
                    the instance is serving xmlrpc, default is 8069
        timeout (int): Timeout value in secs

    Returns:
        True if database exists, False otherwise
    """
    logger.debug("Checking if database exists")
    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=timeout)
    return oerp.db.db_exist(database_name)


def test_connection(db_name, host=False, port=8069, user=False,
                    password=False, timeout=60, only_connection=False):
    """ Checks if the is connection with the instance and parameters are correct

    Args:
        db_name (str): Database name to test connection with
        host (str): Instance server hostname or ip address
        port (int): Instance port to connect
        user (str): user name to test
        password (str): User's password to test
        timeout (int): Desired timeout for test
        only_connection (bool): If true test only connection to the server,
                                otherwise test connection and credentials
    """
    logger.info("Testing connection with '%s' host using '%s' port", host, port)
    try:
        oerp = oerplib.OERP(host, protocol='xmlrpc', port=port, timeout=timeout)
        oerp_version = oerp.db.server_version()
    except socket.error as error_obj:
        if error_obj.errno == 111:
            logger.error("Connection refused, check port number and host")
        return False
    else:
        if oerp_version:
            logger.info("An Odoo v%s server is available" + \
                        " and linstening into %s port", oerp_version, port)
        else:
            logger.warn("Connection could be stablished," + \
                        "but for some reason version number couldn't be gotten")
    if not only_connection:
        try:
            oerp.login(user, password, db_name)
        except oerplib.error.RPCError as error_obj:
            logger.error("%s, please check your parameters and try again", error_obj.message)
            return False
        else:
            logger.info("User '%s' could connect to the" + \
                        "instance properly with the supplied password", user)
    return True

def pase_odoo_configfile(filename):
    """Receive a odoo config file and parse it ti get the parameters needed to backup the database

    Args:
        filename (str): Full path to the Odoo config file

    Returns:
        dict with the needed configuration parameter"""

    config = ConfigParser.ConfigParser()
    res = {}
    try:
        config.readfp(open(filename))
    except IOError:
        logger.error('configuration file "%s" not found',  filename)
        return None
    res.update({'db_host' : config.get('options', 'db_host')})
    res.update({'db_port' : config.get('options', 'db_port')})
    res.update({'db_user' : config.get('options', 'db_user')})
    res.update({'db_password' : config.get('options', 'db_password')})
    res.update({'data_dir' : config.get('options', 'data_dir')})
    
    return res

def pgdump_database(dest_folder, database_config):
    """ Dumps database using pg_dump in sql format

    Args:
        dest_folder (str): Folder where the function will save the dump
        database_config (dict): Database configuration parameters needed to execute pg_dump
    Returns:
        The full dump path and name with .sql extension
    """
    logger.debug("Dumping database %s into %s folder", database_config.get('database'), dest_folder)
    dump_name = os.path.join(dest_folder, 'database_dump.sql')
    os.environ['PGPASSWORD'] = database_config.get('db_password')
    dump_cmd = 'pg_dump {database} -O -f {0} -p {db_port} -h {db_host} -U {db_user}'.format(dump_name, **database_config)
    shell = spur.LocalShell()
    try:
        result = shell.run(shlex.split(dump_cmd))
    except spur.results.RunProcessError as e:
        logger.error('Could not dump database, error message: %s', e.stderr_output)
        return None
    return dump_name

def parse_docker_config(container_name, docker_url="unix://var/run/docker.sock"):
    """Parse env vars from a container to get the nedded parameters to dump the database

    Args:
        container_name: container name or id to be used for the vars extraction
    Returns:
        dict with the needed configuration parameter"""

    cli = Client(base_url=docker_url)
    containers = cli.containers(all=True)
    try:
        inspected = cli.inspect_container(container_name)
    except docker.errors.APIError as error:
        if "no such id" not in error.explanation:
            logger.error("No such container: %s", container_name)
        else:
            logger.error(error.explanation)
        return None
    env_vars = inspected.get('Config').get('Env')
    res = {
        'db_host' : 'localhost',
        'db_port' : 5432,
        'db_user' : 'odoo',
        'db_password' : '',
    }
    for var in env_vars:
        logger.debug('Env var from %s: %s is %s', container_name, var.split('=')[0], var.split('=')[1])
        if var.startswith('DB_PASSWORD='):
            res.update({'db_password': var.split('=')[1]})
        elif var.startswith('DB_USER='):
            res.update({'db_user': var.split('=')[1]})
        elif var.startswith('DB_HOST='):
            ip = var.split('=')[1]
            if '172.17.42.1' == ip:
                ip = '127.0.0.1'
            res.update({'db_host': ip})
        elif var.startswith('DB_PORT='):
            res.update({'db_port': var.split('=')[1]})
    volumes = inspected.get('Volumes')
    for mnt, volume in volumes.iteritems():
        if '.local/share/Odoo' in mnt and volume:
            res.update({'data_dir': volume})
            break
    else:
        logger.error('Datadir not found, wont be able to backup attachments')

    if not res.get('data_dir'):
        logger.error('The attachments dicrectory was not mounted from the host, wont be able to backup attachments')
    return res
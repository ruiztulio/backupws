 # -*- encoding: utf-8 -*- 
import oerplib
import shutil
import datetime                                                                                                                                                                           
import tarfile
import os
import bz2
import logging
import argparse
import socket

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')

parser = argparse.ArgumentParser()
parser.add_argument("db", help="Database name", default=False)
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
USER = 'nhomar@vauxoo.com'
PASSWORD = '4DM1NCHUCK'


oerp = oerplib.OERP(HOST, protocol='xmlrpc', port=PORT)

try:
    user = oerp.login(USER, PASSWORD, DATABASE)
except socket.error as e:
    if e.errno == 111:
        logger.critical('Cannot connect to OpenERP Server')
        logger.critical('Check instance address and server')
        logger.critical('Program terminating')
        sys.exit(1)
    else:
        raise

logger.info("Deactivating mail servers")
mail_ids = oerp.search('ir.mail_server', [('active', '=', True)])
if mail_ids:
    logger.debug("Mail server ids %s", str(mail_ids))
    oerp.write('ir.mail_server', mail_ids, {'active': False})

logger.info("Deactivating out")
partner_ids = oerp.search('res.partner', [('opt_out', '=', False)])
if partner_ids:
    logger.debug("Partner ids %s", str(partner_ids))
    oerp.write('res.partner', partner_ids, {'opt_out': True})

logger.info("Deactivating PAC params")
pac_ids = oerp.search('params.pac', [('active', '=', True)])
if pac_ids:
    logger.debug("Pac ids %s", str(pac_ids))
    oerp.write('params.pac', pac_ids, {'active': False})

logger.info("Deactivating cron jobs")
cron_ids = oerp.search('ir.cron', [('model', '<>', 'osv_memory.autovacuum'), ('active', '=', True)])
if cron_ids:
    logger.debug("Cron ids %s", str(cron_ids))
    oerp.write('ir.cron', cron_ids, {'active': False})



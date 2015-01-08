 # -*- encoding: utf-8 -*- 
import oerplib
import logging
import sys
import argparse
import socket
from lib import utils

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backup')


def deactivate(db_name, user_login, user_password,
               host='localhost', port=8069):
    """ Deactivate some instance parameters to avoid troubles (mail, cron, pac, etc)

    Args:
        db_name (str): Database name to be deactivated
        user_login (str): Login name to use when connecting to the database
        user_password (str): User password to connect
        host (str): Hostname or ip to conect
        port (int): Instance port number
    """

    oerp = oerplib.OERP(host, protocol='xmlrpc', port=port)

    try:
        oerp.login(user_login, user_password, db_name)
    except socket.error as eror_obj:
        if eror_obj.errno == 111:
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

    partner = oerp.browse('res.partner', 1)
    if hasattr(partner, 'opt_out'):
        logger.info("Deactivating out")
        partner_ids = oerp.search('res.partner', [('opt_out', '=', False)])
        if partner_ids:
            logger.debug("Partner ids %s", str(partner_ids))
            oerp.write('res.partner', partner_ids, {'opt_out': True})

    params = oerp.search('ir.model', [('name', '=', 'params.pac')])
    if params:
        logger.info("Deactivating PAC params")
        pac_ids = oerp.search('params.pac', [('active', '=', True)])
        if pac_ids:
            logger.debug("Pac ids %s", str(pac_ids))
            oerp.write('params.pac', pac_ids, {'active': False})

    logger.info("Deactivating cron jobs")
    cron_ids = oerp.search('ir.cron', [('model', '<>', 'osv_memory.autovacuum'),
                                       ('active', '=', True)])
    if cron_ids:
        logger.debug("Cron ids %s", str(cron_ids))
        retry = 3
        while retry >= 0:
            try:
                oerp.write('ir.cron', cron_ids, {'active': False})
            except oerplib.error.RPCError as eror_obj:
                retry -= 1
                if retry == -1:
                    raise
                logger.warn("Error while trying to deactivate cron jobs, let's try again")
            else:
		retry = -2

def main(main_args):
    """ Main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Database name", default=False)
    parser.add_argument("-t", "--temp_dir", help="", default="/tmp")
    parser.add_argument("-d", "--backup_dir", help="/var/lib/postgresql/db_backup", default=".")
    parser.add_argument("-H", "--host", help="", default="localhost")
    parser.add_argument("-p", "--port", help="", default=8069)
    parser.add_argument("-u", "--user", help="Odoo super user", default="admin")
    parser.add_argument("-w", "--password", help="Odoo super user pass", default="admin")

    args = parser.parse_args(main_args)
    if not utils.test_connection(args.db, args.host, args.port, args.user, args.password):
        return 1
    deactivate(args.db, args.user, args.password, args.host, args.port)


if __name__ == '__main__':
    logger.info("Starting deactivate process")
    sys.exit(main(sys.argv[1:]))
    logger.info("Resore deactivate has finished")

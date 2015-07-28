"""Deactivates a database
"""
# -*- encoding: utf-8 -*-

import configargparse
import sys
import psycopg2
import logging
import uuid
from lib import utils

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def deactivate(sqls, str_conn, actions, rpass=False):
    """Deactivates some database's parameters to avoid problems

    Args:
        sqls: Query dictionary to execute
        str_conn: Database's connection string
        actions: Actions to be applied
        rpass: Updating users' passwords
    """
    logger.info('Connecting to postgres server')
    try:
        logger.debug('Connection string: "%s"', str_conn)
        conn = psycopg2.connect(str_conn)
        conn.set_isolation_level(0)
    except Exception as error:
        logger.exception('Connection not established: %s', error.message)
        raise

    cur = conn.cursor()
    logger.info('Executing queries')
    for name in actions:
        try:
            logger.info(' - Executing %s ', name)
            logger.debug('Query: "%s"', sqls.get(name))
            cur.execute(sqls.get(name))
        except psycopg2.ProgrammingError as error:
            if 'does not exist' in error.message:
                logger.warn("Couldn't be executed in database: %s", error.message.strip())
            else:
                raise

    if rpass:
        logger.info("Updating users' passwords")
        cur.execute("SELECT id from res_user")
        users = cur.fetchall()
        for user in users:
            try:
                logger.info(' - Updating %s ', user[0])
                cur.execute("UPDATE res_user SET password = '%s' WHERE id = %s" % \
                            str(uuid.uuid4().get_hex().upper()[0:6]), user[0])
            except Exception as error:
                logger.exception("Couldn't be executed in database: %s",
                                 error.message)
                raise
    cur.close()
    conn.close()


def main(main_args):
    """Main function
    """
    parser = configargparse.ArgParser()
    parser.add("-d", "--database", help="Database name")
    parser.add("-U", "--username", help="Database username", default=False)
    parser.add("-W", "--password", help="User password", default=False)
    parser.add("-H", "--host", help="Database server host or socket",
               default=False)
    parser.add("-p", "--port", help="Database server port", default=False)
    parser.add("-r", "--rpass", help="Generate random passwords for users",
               default=False)
    parser.add("-a", "--actions",
               help="""Comma separated actions to execute (deactivates)
                    possibles actions: partner, in_mail, out_mail, pac, cron, rpass""",
               default=False)
    parser.add("-f", "--from_docker",
               help="Docker container which has the database configuration",
               default=False)

    args = parser.parse_args(main_args)
    utils.check_installation()
    logger.info('Initiating parameters')

    sqls = {
        'partner': "UPDATE res_partner SET opt_out = True;",
        'out_mail': "UPDATE ir_mail_server SET active = False, smtp_user = 'user', smtp_pass = 'pass';",
        'in_mail': "UPDATE fetchmail_server SET active = False, \"user\" = 'user', password = 'pass';",
        'pac': "UPDATE params_pac SET active = False;",
        'cron': "UPDATE ir_cron SET active = False WHERE model <> 'osv_memory.autovacuum';",
        'notify': "UPDATE res_partner SET notify_email = 'none'"
    }

    str_conn = '''dbname=%s''' % (args.database)

    if args.actions:
        actions = [x.strip() for x in args.actions.split(',')]
    else:
        actions = sqls.keys()

    if args.from_docker:
        config = utils.parse_docker_config(args.from_docker)
        str_conn = '{0} password={db_password} user={db_user} host={db_host} port={db_port}' \
                   .format(str_conn, **config)
    else:
        if args.password:
            str_conn = '%s password=%s' % (str_conn, args.password)
        if args.username:
            str_conn = '%s user=%s' % (str_conn, args.username)
        if args.host:
            str_conn = '%s host=%s' % (str_conn, args.host)
        if args.port:
            str_conn = '%s port=%s' % (str_conn, args.port)

    deactivate(sqls, str_conn, actions, args.rpass)


if __name__ == '__main__':
    logger.info("Starting deactivate process")
    sys.exit(main(sys.argv[1:]))
    logger.info("Deactivate process finished")

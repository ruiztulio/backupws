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


def connect(str_conn):
    """Connect to a postgres database

    Args:
        str_conn: Database's connection string
    Return:
        Dictionary with connection and cursor
    """
    logger.info('Connecting to postgres server')
    try:
        logger.debug('Connection string: "%s"', str_conn)
        conn = psycopg2.connect(str_conn)
        conn.set_isolation_level(0)
    except Exception as error:
        logger.exception('Connection not established: %s', error.message)
        conn_dict = False
        raise

    cur = conn.cursor()
    conn_dict = {
        'conn': conn,
        'cursor': cur
    }
    return conn_dict


def disconnect(conn):
    """Disconnets from a postgres database

    Args:
        conn: Connection dictionary
    """
    conn['cursor'].close()
    conn['conn'].close()


def deactivate(conn, sqls, actions):
    """Deactivates some database's parameters to avoid problems

    Args:
        sqls: Query dictionary to execute
        actions: Actions to be applied
        conn: Connection dictionary
    """
    logger.info('Executing queries')
    for name in actions:
        try:
            logger.info(' - Executing %s ', name)
            logger.debug('Query: "%s"', sqls.get(name))
            conn['cursor'].execute(sqls.get(name))
        except psycopg2.ProgrammingError as error:
            if 'does not exist' in error.message:
                logger.warn("Couldn't be executed in database: %s",
                            error.message.strip())
            else:
                raise


def passwords(conn):
    """Updates users' passwords

    Args:
        conn: Connection dictionary
    """
    logger.info("Updating users' passwords")
    conn['cursor'].execute("SELECT id from res_user")
    users = conn['cursor'].fetchall()
    for user in users:
        try:
            logger.info(' - Updating %s ', user[0])
            conn['cursor'].execute("UPDATE res_user SET password = '%s' WHERE id = %s" % \
                                   str(uuid.uuid4().get_hex().upper()[0:6]), user[0])
        except Exception as error:
            logger.exception("Couldn't be executed in database: %s",
                             error.message)
            raise


def get_sqls():
    """Creates sql queries dictionary

    Return:
        Dictionary of sql.
    """
    sql_dict = {
        'partner': "UPDATE res_partner SET opt_out = True;",
        'out_mail': ("UPDATE ir_mail_server"
                     " SET active = False,"
                     " smtp_user = 'user', smtp_pass = 'pass';"),
        'in_mail': ("UPDATE fetchmail_server"
                    " SET active = False, \"user\" = 'user', "
                    "password = 'pass';"),
        'pac': "UPDATE params_pac SET active = False;",
        'cron': ("UPDATE ir_cron SET active = False"
                 " WHERE model <> 'osv_memory.autovacuum';"),
        'notify': "UPDATE res_partner SET notify_email = 'none'",
        'ir_action': ("UPDATE base_action_rule SET active = False"
                      " WHERE name LIKE '%Create Sale from Purchase%'")
    }
    return sql_dict


def get_conn(args):
    """Creates connection string from arguments

    Args:
        args: Parsed arguments
    Return:
        Connection string
    """
    str_conn = '''dbname=%s''' % (args.database)
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
    return str_conn


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
                    possibles actions: partner, in_mail, out_mail, pac, cron, rpass, ir_action""",
               default=False)
    parser.add("-f", "--from_docker",
               help="Docker container which has the database configuration",
               default=False)

    args = parser.parse_args(main_args)
    utils.check_installation()
    logger.info('Initiating parameters')

    sqls = get_sqls()
    if args.actions:
        actions = [x.strip() for x in args.actions.split(',')]
    else:
        actions = sqls.keys()

    str_conn = get_conn(args)

    conn = connect(str_conn)
    if conn:
        deactivate(conn, sqls, actions)
        if args.rpass:
            passwords(conn)
        disconnect(conn)


if __name__ == '__main__':
    logger.info("Starting deactivate process")
    sys.exit(main(sys.argv[1:]))
    logger.info("Deactivate process finished")

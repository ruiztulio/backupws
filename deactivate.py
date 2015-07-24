# -*- encoding: utf-8 -*-

import configargparse
import psycopg2
import getpass
import logging
import uuid
from lib import utils

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = configargparse.ArgParser()
parser.add("-d", "--database", help="Database name")
parser.add("-U", "--username", help="Database username", default=False)
parser.add("-W", "--password", help="User password", default=False)
parser.add("-H", "--host", help="Database server host or socket", default=False)
parser.add("-p", "--port", help="Database server port", default=False)
parser.add("-r", "--rpass", help="Generate random passwords for users", default=False)
parser.add("-a", "--actions", help="""Comma separated actions to execute (deactivates)
                                    possibles actions: partner, in_mail, out_mail, pac, cron, rpass""", 
    default=False)
parser.add("-f", "--from_docker", help="Docker container which has the database configuration", 
    default=False)

args = parser.parse_args()
utils.check_installation()
logger.info('Inicializando parametros')

sqls = {
    'partner' : "UPDATE res_partner SET opt_out = True;",
    'out_mail' : "UPDATE ir_mail_server SET active = False, smtp_user = 'user', smtp_pass = 'pass';",
    'in_mail' : "UPDATE fetchmail_server SET active = False, \"user\" = 'user', password = 'pass';",
    'pac' : "UPDATE params_pac SET active = False;",
    'cron' : "UPDATE ir_cron SET active = False WHERE model <> 'osv_memory.autovacuum';",
    'notify' : "UPDATE res_partner SET notify_email = 'none'"
}

str_conn = '''dbname=%s''' % \
            (args.database)

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
        str_conn = '%s password=%s'%(str_conn, args.password)
    if args.username:
        str_conn = '%s user=%s'%(str_conn, args.username)
    if args.host:
        str_conn = '%s host=%s'%(str_conn, args.host)
    if args.port:
        str_conn = '%s port=%s'%(str_conn, args.port)

logger.info('Estableciendo conexion con el servidor postgres')
try:
    logger.debug('Cadena de conexion: "%s"', str_conn)
    conn = psycopg2.connect(str_conn)
    conn.set_isolation_level(0)
except Exception as e:
    logger.exception('No se pudo conectar a la base de datos: %s' % e.message)
    raise

cur = conn.cursor()
logger.info('Ejecutando consultas')
for name in actions:
    try:
        logger.info(' - Ejecutando %s ' % name)
        logger.debug('Query: "%s"', sqls.get(name))
        cur.execute(sqls.get(name))
    except Exception as e:
        logger.warn('No se pudo ejecutar a la base de datos: %s' % e.message)

if args.rpass:
    logger.info('Actualizando claves de usuarios')
    cur.execute("SELECT id from res_user")
    users = cur.fetchall()
    for user in users:
        try:
            logger.info(' - Actualizando %s ' % user[0])
            cur.execute("UPDATE res_user SET password = '%s' WHERE id = %s" % \
                str(uuid.uuid4().get_hex().upper()[0:6]), user[0])
        except Exception as e:
            logger.exception('No se pudo ejecutar a la base de datos: %s' % e.message)
            raise

cur.close()
conn.close()
logger.info('Finalizado')

backupws
========

A simple set of python scripts to make an Odoo 8.0 backup using oerplib, in this way you can backup and restore attacments

## Backup

To Backup a database you must run (if Odoo server is on localhost and serving on default port)::

    python backup_ws.py database_name

Else:

    python backup_ws.py database_name -H host_name -p odoo_xml_rpc_port

Other parameters can be user, to see how just run:

    python backup_ws.py --help

## Restore

To restore a backup made with **backup_ws.py** (if Odoo server is on localhost and serving on default port)::
    
    python restore_db_ws.py database_name -f route/to/file.tar.bz2

Else:

    python restore_db_ws.py database_name -H host_name -p odoo_xml_rpc_port -f route/to/file.tar.bz2

Database name and file are mandaroty fields

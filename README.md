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

## Branches

To save branches' info into a json file::

    python branches.py -f json_file -p path_to_be_saved -s

If path_to_be_saved is not specified, current dir will be used
Json_file is a mandatory field

To build branches using Json file made with **branches.py**::

    python branches.py -f json_file -l

If some depth is required for cloned branches, use depth parameter::

    python branches.py -f json_file -d depth -l

Json_file is a mandatory field

backupws
========

A simple set of python scripts to make an Odoo 8.0 backup using oerplib, in this way you can backup and restore attacments

## Backup

To Backup a database you must run (if Odoo server is on localhost and serving on default port):

    python backup_ws.py database_name

Else:

    python backup_ws.py database_name -H host_name -p odoo_xml_rpc_port

Other parameters can be user, to see how just run:

    python backup_ws.py --help

## Restore

To restore a backup made with **backup_ws.py** (if Odoo server is on localhost and serving on default port):
    
    python restore_db_ws.py database_name -f route/to/file.tar.bz2

Else:

    python restore_db_ws.py database_name -H host_name -p odoo_xml_rpc_port -f route/to/file.tar.bz2

Database name and file are mandaroty fields

If you get a memory error when trying to restore the database and you are using docker you can use:

    python restore_db.py -d database_name -f docker_name_or_id -b route/to/file.tar.bz2

Note that the previous command does not use web services to restore the database and asumes that you started the container using the [deployment templates](https://github.com/Vauxoo/deploy-templates/tree/master/ansible), this script reads the env vars that was created in the [env section](https://github.com/Vauxoo/deploy-templates/blob/master/ansible/start.yml#L16)

## Branches

To save branches' info into a json file::

    python branches.py -f json_file -p path_of_repo_structure -s

To build branches using Json file made with **branches.py**::

    python branches.py -f json_file -p path_of_repo_structure -l

To update branches to commits specified in Json file::

    python branches.py -f json_file -p path_of_repo_structure --repo comma_separated_list_of_repo -u

To pull branches from their origin urls::

    python branches.py -f json_file -p path_of_repo_structure --repo comma_separated_list_of_repo --pull

If path_of_repo_structure is not specified, current dir will be used
Json_file is a mandatory field

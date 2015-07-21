BACKUPWS
========

A simple set of python scripts to make an Odoo 8.0 backup using oerplib, in this way you can backup and restore attacments, deactivate databases and easily manipulate git branches

# BACKUP

## Using ws

To Backup a database using ws you must run (if Odoo server is on localhost and serving on default port):

    python backup_db_ws.py database_name -d backup_dir

Else:

    python backup_db_ws.py database_name -H host_name -p odoo_xml_rpc_port -d backup_dir

Other parameters that can be used are:
* -t: Temp working dir
* -r: Reason why backup is being done
* -u: Odoo superuser
* -w: Superuser password

All these options can be consulted any time by just running:

    python backup_db_ws.py --help

## Using docker container

To backup a database without running ws you must run:

    python backup_db.py -d database_name -o odoo_configfile -b backup_dir

Or:

    python backup_db.py -d database_name -f docker_container -b backup_dir

Options -o and -f are mutually exclusive. Other parameters that can be used are:
* -t: Temp working dir
* -r: Reason why backup is being done
* -c: Optional config file

All these options can be consulted any time by just running:

    python backup_db.py --help

#RESTORE

## Using ws

To restore a backup made with **backup_db_ws.py** (if Odoo server is on localhost and serving on default port):
    
    python restore_db_ws.py database_name -f route_to_file.tar.bz2

Else:

    python restore_db_ws.py database_name -H host_name -p odoo_xml_rpc_port -f route_to_file.tar.bz2

Other parameters that can be used are:
* -t: Temp working dir
* -u: Odoo superuser
* -w: Superuser password

All these options can be consulted any time by just running:

    python restore_db_ws.py --help

Database name and file are mandaroty fields

## Using docker container

To restore a database without running ws you must run:

    python restore_db.py -d database_name -o odoo_configfile -b backup_file

Or:

    python restore_db.py -d database_name -f docker_container -b backup_file

Options -o and -f are mutually exclusive. Other parameters that can be used are:
* -t: Temp working dir
* -c: Optional config file

All these options can be consulted any time by just running:

    python restore_db.py --help

# DEACTIVATE

## Using ws

To deactivate a database using ws you must run (if Odoo server is on localhost and serving on default port)::

    python deactivate_ws.py database_name

Else:

    python deactivate_ws.py database_name -H host_name -p odoo_xml_rpc_port

Other parameters that can be used are:
* -u: Odoo superuser
* -w: Superuser password

All these options can be consulted any time by just running:

    python deactivate_ws.py --help

## Without use ws

To deactivate a database without ws run:

    python deactivate.py database_name

Else:

    python deactivate.py database_name -H host_name -p odoo_xml_rpc_port

Other parameters that can be used are:
* -U: Database username
* -W: User password
* -r: Generate random passwords for users
* -a: Comma separated actions to execute (possible actions: partner, cron, mail, pac, notify)
* -f: Docker container which have the database configuration

All these options can be consulted any time by just running:

    python deactivate.py --help

# TEST DATABASE

Test databases are created using backup modules and configurations defined in a Json config file with the following structure:

{
    type:{
        "host":"host of database",
        "port":{
            "xmlrpc":odoo xmlrpc port,
            "opt":optional port
        },
        "user":"database user",
        "pswd":"password",
        "superuser":"database superuser",
        "superpswd":"superuser password"
    },

    ...
}

To create a test database from a backup file run:

    python test_db.py -f backup_file --config-file json_config_file --config config_type_selected

To create a test database using the latest backup file in a backup dir:

    python test_db.py -p backup_path --config-file json_config_file --config config_type_selected

To create a test database from an existing and active database:

    python test_db.py -d origin_database --config-file json_config_file --config config_type_selected --active-config-file json_config_file_for_origin_db

Other parameters that can be used:
* --log-level: Level for logger
* --logfile: File where store logs
* --temp-dir: Temp working dir

# DISK ALERT

Evaluates partitions of hard disks and send alerts if they're running out of space.
To evaluate a group of partitions you must run:

    python disk_alert.py -P comma_separated_list_of_partitions -F sender_email_address -W password -T comma_separated_list_of_recipients -L space_limit_for_red_alert

Other parameters that can be used:
* --log-level: Level for logger
* --logfile: File where store logs
* --server: SMTP service server in the form "server:port"

## Branches

To save branches' info into a json file::

    python branches.py -f json_file -p path_of_repo_structure -s

To build branches using Json file made with **branches.py**::

    python branches.py -f json_file -p path_of_repo_structure -l

To update branches using Json file::

    python branches.py -f json_file -p path_of_repo_structure --repo comma_separated_list_of_repo -u

To reset branches to commits in Json file::

    python branches.py -f json_file -p path_of_repo_structure --repo comma_separated_list_of_repo -r

If path_of_repo_structure is not specified, current dir will be used
Json_file is a mandatory field

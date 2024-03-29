#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = '''
---
module: postgresql_exec
author: Mohamed Amine Jarboui
version_added: "never"
short_description: Executes a SQL script in PostgreSQL.
description:
  - This module is intended for initializing database schema and maybe
    populating with some seed data from a SQL script. However, it can be used
    to execute any SQL commands. It is up to the user to maintain idempotence.
options:
  src:
    description:
      - Path of a SQL file on the local machine; can be absolute or relative.
        If the path ends with C(.j2), then it is considered as a Jinja2
        formatted template.
      - When C(remote_src=yes), then it means path on the remote machine
        instaed (templating is not supported in this mode).
    required: false
  remote_src:
    description:
      - If C(no), the script file will be copied from the local machine,
        otherwise it will be located on the remote machine.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  content:
    description:
      - When used instead of C(src), execute SQL commands specified as the value.
    required: false
  database:
    description:
      - Name of the database to connect to.
    required: true
    aliases: [ "db" ]
  host:
    description:
      - The database host address. If unspecified, connect via Unix socket.
    aliases: [ "login_host" ]
    required: false
  port:
    description:
      - The database port to connect to.
    required: false
    default: "5432"
  user:
    description:
      - The username to authenticate with.
    aliases: [ "login_user", "login" ]
    required: false
    default: "postgres"
  password:
    description:
      - The password to authenticate with.
    aliases: [ "login_password" ]
    required: false
notes:
  - This module requires Python package I(psycopg2) to be installed on the
    remote host. In the default case of the remote host also being the
    PostgreSQL server, PostgreSQL has to be installed there as well, obviously.
    For Debian/Ubuntu-based systems, install packages I(postgresql) and
    I(python-psycopg2). For Gentoo system, install packages
    I(dev-db/postgresql-server) and I(dev-python/psycopg).
requirements: [psycopg2]
'''

EXAMPLES = '''
# Execute SQL script located in the files directory.
- postgresql_exec: 
    src=script.sql
    host=db.example.org
    database=foodb
    user=foodb
    password=top-secret
# Execute templated SQL script located in the templates directory.
- postgresql_exec: 
    src=script.sql.j2
    database=foodb
    user=foodb
# Execute /tmp/script.sql located on the remote (managed) system.
- postgresql_exec: 
    remote_src=yes
    src=/tmp/script.sql
    database=foodb
    user=foodb
'''

try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    psycopg2 = None


def readfile(path):
    f = open(path, 'r')
    try:
        return f.read()
    finally:
        f.close()


def main():
    module = AnsibleModule(
        argument_spec={
            'content':    {'no_log': True},
            'remote_src': {'default': False, 'type': 'bool'},
            'database':   {'required': True, 'aliases': ['db']},
            'host':       {'default': '', 'aliases': ['login_host']},
            'port':       {'default': 5432, 'type': 'int'},
            'user':       {'default': 'postgres', 'aliases': ['login_user', 'login']},
            'password':   {'default': '', 'aliases': ['login_password'], 'no_log': True},
            'src':        {},  # used in postgresql_exec plugin runner to load content from file
        },
        required_one_of=[['src', 'content']],
        supports_check_mode=True
    )

    if not psycopg2:
        module.fail_json(msg='Python module "psycopg2" must be installed.')

    # Create type object as namespace for module params
    p = type('Params', (), module.params)

    if p.remote_src and p.src:
        try:
            script = readfile(p.src)
        except IOError, e:
            module.fail_json(msg=str(e))
    else:
        script = p.content

    # To use defaults values, keyword arguments must be absent, so check which
    # values are empty and don't include in the **db_params dictionary.
    db_params = dict((k, v) for (k, v) in module.params.iteritems()
                     if k in ['host', 'port', 'user', 'password', 'database'] and v != '')

    # Connect to Database
    try:
        dbconn = psycopg2.connect(**db_params)
        cursor = dbconn.cursor()
    except Exception, e:
        module.fail_json(msg="unable to connect to database: %s" % e)

    try:
        cursor.execute(script)

    except psycopg2.Error, e:
        dbconn.rollback()
        # psycopg2 errors come in connection encoding, reencode
        msg = e.message.decode(dbconn.encoding).encode(sys.getdefaultencoding(), 'replace')
        module.fail_json(msg=msg)

    if module.check_mode:
        dbconn.rollback()
    else:
        dbconn.commit()

    module.exit_json(changed=True)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()


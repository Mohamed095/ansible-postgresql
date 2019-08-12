#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path
import time

"""
Ansible module to check karaf features installed
(c) 2017, Matthieu Rémy <remy.matthieu@gmail.com>
"""

DOCUMENTATION = '''
---
module: karaf_feature_check
short_description: Check Karaf features.
description:
    - Check Karaf features installed or not.
options:
    name:
        description:
            - name of the feature to install or uninstall
        required: true
        default: null
    version:
        description:
            - version of the feature to install or uninstall
        required: false
        default: null
    client_bin:
        description:
            - path to the 'client' program in karaf, can also point to the root of the karaf installation '/opt/karaf'
        required: false
        default: /opt/karaf/bin/client
'''

EXAMPLES = '''
# Check if karaf feature installed
- karaf_feature: name="camel-jms"

# Check if karaf feature versionned installed
- karaf_feature: name="camel-jms" version="2.18.1"

'''

FEATURE_STATE_UNINSTALLED = 'Uninstalled'
CLIENT_KARAF_COMMAND = "{0} 'feature:{1}'"

_KARAF_COLUMN_SEPARATOR = '|'

def is_feature_installed(client_bin, module, feature_name, feature_version):
    """ Check if a feature with given version is installed.

    :param client_bin: karaf client command bin
    :param module: ansible module
    :param feature_name: name of feature to install
    :param feature_version: version of feature to install. Optional.
    :return: True if feature is installed, False if not
    """

    cmd = CLIENT_KARAF_COMMAND.format(client_bin, 'list -i')
    rc, out, err = module.run_command(cmd)
    lines = out.split('\n')
    
    if not feature_version:
        feature_version = ''

    # Feature version in karaf use . instead of - when feature is deployed.
    # For instance, snapshot version will be 1.0.0.SNAPSHOT instead of 1.0.0-SNAPSHOT
    feature_version = feature_version.replace('-', '.')

    is_installed = False
    installed = 'absent'
    for line in lines:
        feature_data = line.split(_KARAF_COLUMN_SEPARATOR)
        if len(feature_data) < 4:
            continue
        
        name = feature_data[0].strip()
        version = feature_data[1].strip()
        state = feature_data[3].strip()
        
        if name != feature_name:
            continue
        
        if state != FEATURE_STATE_UNINSTALLED:
            if feature_version:
                if version == feature_version:
                    installed = 'installed'
                    is_installed = True
                    return is_installed, installed
            else:
                installed = 'installed'
                is_installed = True
                return is_installed, installed

    return is_installed, installed

def check_client_bin_path(client_bin):
    if os.path.isfile(client_bin):
        return client_bin
    
    if os.path.isdir(client_bin):
        test = os.path.join(client_bin, 'bin/client')
        if os.path.isfile(test):
            return test
    else:
        raise Exception('client_bin parameter not supported: %s' % client_bin)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            version=dict(default=None),
            client_bin=dict(default="/opt/karaf/bin/client", type="path")
        )
    )

    name = module.params["name"]
    version = module.params["version"]
    client_bin = module.params["client_bin"]

    client_bin = check_client_bin_path(client_bin)

    is_installed, installed = is_feature_installed(client_bin, module, name, version)

    module.exit_json(changed=is_installed, installed=installed, name=name)

if __name__ == '__main__':
    main()

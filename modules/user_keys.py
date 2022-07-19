#!/usr/bin/python
'''
 Description:
  Ansible module to 
  1. create a string of all keys for a list of users
'''

import traceback
import os
import yaml
import subprocess
from ansible.module_utils.basic import AnsibleModule

USERS_LIST = {
    "users": {"required": False, "type": "list"}
}

class GenericScalar(object):
    ''' Generic class to handle tags prefixed with exclamation mark(!) '''
    def __init__(self, value, tag, style=None):
        self.value = value
        self.tag = tag
        self.style = style

    @staticmethod
    def to_yaml(dumper, data):
        ''' data is a generic scalar '''
        return dumper.represent_scalar(data.tag, data.value, style=data.style)

def default_constructor(loader, tag_suffix, node):
    ''' Define generic constructor to handle tags prefixed with exclamation mark(!) '''
    if isinstance(node, yaml.ScalarNode):
        return GenericScalar(node.value, tag_suffix, style=node.style)
    else:
        raise NotImplementedError('Node: ' + str(type(node)))

def validate_users(users):
    ''' Method to validate users data '''
    req_fields = ['name', 'state', 'sudo', 'key']
    for usr in users:
        for fld in req_fields:
            if fld not in usr.keys():
                raise ValueError('mandatory field [%s] missing in %s' % (fld, usr))

            if not str(usr[fld]).strip():
                raise ValueError('mandatory field [%s] value cannot be empty [%s]' % (fld, usr))


def main():
    ''' Method to process user_keys from Ansible '''
    module = AnsibleModule(argument_spec=USERS_LIST, supports_check_mode=True)
    errorcode = 0
    try:
        users_list = module.params['users']
        bsa_key = 'id_rsa_bsa.pub'
        res = ""
        if not users_list:
            errorcode = 2
            raise ValueError("'users' list cannot be empty.")
        else:
            validate_users(users_list)

        keys_path =  os.path.join(os.getcwd(), 'sshkeys') + '/'
             
        for user_dict in users_list:
            #add SSH authorized key to a string
            for item in user_dict['key']:
                with open(keys_path + item , "r") as kfo:
                    str_keyinfo = kfo.read().replace('\n', '')
                    res += item + '|' + str_keyinfo + '|'
                
        with open(keys_path + bsa_key , "r") as kfo:
            str_keyinfo = kfo.read().replace('\n', '')
            res += bsa_key + '|' + str_keyinfo
            
    except : #ValueError, vearg:
        errmsg = str(vearg) + ' stacktrace = {' + str(traceback.format_exc()) + '}'
        module.fail_json(msg=errmsg)

    localchanged = True if errorcode == 0 else False
    #module.exit_json(change=localchanged, meta=res)
    results = dict(changed=False, key_str=dict(kestr = res))
    module.exit_json(**results)


if __name__ == "__main__":
    main()

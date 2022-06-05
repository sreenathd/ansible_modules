#!/usr/bin/python
'''
 Description:
  Ansible module to 
  1. merge different types of users lists
  2. Create Users
  3. Grant sudo permission
  4. Verify whether user exists
  5. Add SSH authorized keys for user
  6. Add SSH authorized keys for root
'''

import traceback
import os
import yaml
from ansible.module_utils.basic import AnsibleModule

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

def get_users_from_group_file():
    ''' Method to read the users list defined in group file'''
    yaml.add_multi_constructor('', default_constructor, Loader=yaml.SafeLoader)
    yaml.add_representer(GenericScalar, GenericScalar.to_yaml, Dumper=yaml.SafeDumper)

    # read global file all.yaml
    glob_file = os.path.join(os.getcwd(), 'group_vars', 'all.yaml')
    glob_obj = open(glob_file, "r")
    glob_content = yaml.safe_load(glob_obj)

    new_lst_users = []
    for item in glob_content:
        if 'dev_users' in item or 'sys_admin_users' in item or 'alimas_users' in item:
            for i in glob_content[item] :
                new_lst_users.append(i)
    
    return new_lst_users

class user_op:

    def run_cmd(self,cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if output:
            output = output.strip().decode("utf-8")
        if error:
            error = error.decode("utf-8")
        if p.returncode != 0:
            print(error)
            #raise Exception("Error")
        return output

    # Create Users
    def user_add(self, username):
        cmd = ["useradd", username]
        return self.run_cmd(cmd)

    # Grant sudo permission
    def user_add_sudo(self , username, user_dir=None):
        cmd = ["usermod", "-a", "-G" , username]
        return self.run_cmd(cmd)

    # Verify whether user exists
    def user_verify( self, username):
        ps = subprocess.Popen(('getent', 'passwd', username), stdout=subprocess.PIPE)
        output, error = ps.communicate()
        if output:
            output = output.strip().decode("utf-8")
        if error :
            error = error.decode("utf-8")
        if username in output :
            print("user is present")
        return output

    # Add SSH authorized keys for user
    def add_authorised_key(self, key_file):
        cmd = ["cat", key_file, ">>", "~/.ssh/authorized_keys"]
        return self.run_cmd(cmd)

    #Add SSH authorized keys for root user
    def add_root_authorised_key(self, key_file):
        cmd = ["cat", key_file, ">>", "/root/.ssh/authorized_keys"]
        return self.run_cmd(cmd)
    

def main():
    ''' Method to process user_list from Ansible '''
    module = AnsibleModule(supports_check_mode=True)
    errorcode = 0
    try:
        users_list = get_users_from_group_file()
        keys_path =  os.path.join(os.getcwd(), 'sshkeys') + '/'
        #'~/bootstrap/ansible/sshkeys/'
        for user_dict in users_list:
            if 'present' == user_dict['state']:
                #add the user
                user_ops.user_add(user_dict['name'])

                #grant sudo permission
                if 'present' == user_dict['sudo']:
                    user_ops.user_add_sudo(user_dict['name'])

                #verify whether user exists
                user_ops.user_verify(user_dict['name'])

                #add SSH authorized key
                for item in user_dict['key']:
                    user_ops.add_authorised_key(keys_path + item)

                #add id_rsa_bsa.pub key to the root user's authorized_keys
                user_ops.add_root_authorised_key(keys_path + 'id_rsa_bsa.pub')

                #add id_rsa_bsa.pub key to the bsa user's authorized_keys
                user_ops.add_authorised_key(keys_path + 'id_rsa_bsa.pub')
        
    except ValueError, vearg:
        errmsg = str(vearg) + ' stacktrace = {' + str(traceback.format_exc()) + '}'
        module.fail_json(msg=errmsg)
    except Exception, earg:
        errmsg = str(earg) + ' stacktrace = {' + str(traceback.format_exc()) + '}'
        module.fail_json(msg=errmsg)
    else:
        localchanged = True if errorcode == 0 else False
        module.exit_json(change=localchanged, meta=res)

if __name__ == "__main__":
    main()

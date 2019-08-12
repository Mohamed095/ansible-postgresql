#!/usr/bin/python
DOCUMENTATION = '''

---
module: get_checksum
Author: MOHAMED AMINE JARBOUI
Supervisor: KAIS ENNAIFAR
short_description: Get the sha1 & md5 from Nexus 3 repository 
'''

EXAMPLES = '''
- name: test get_checksum module
  hosts: elasticsearch
  become: yes
  remote_user: root
  tasks:
    - name: mymodule
      get_checksum:
        raw: dyco-raw
        repo: elasticsearch
        option: bin
        version: 5.4.0
        hash_type: md5
      register: result

    - name: Get value
      debug: var=result.msg

EXAMPLE OF URL:
#url: "http://ip:8081/service/rest/v1/search?repository=dyco-raw&group=/elasticsearch/bin/5.4.0"

'''

from ansible.module_utils.basic import *
import urllib
import json
import os.path

list= ["sha1", "md5"] 


def get_checksum(raw,repo,option,version,address,hash_type):
  url= "http://"+ address +":"+port+"/service/rest/v1/search?repository="+raw+"&group=/"+repo+"/"+option+"/"+version
  if hash_type  in list:
     res = urllib.urlopen(url)
     data = json.loads(res.read())
     value = data["items"][0]["assets"][0]["checksum"][hash_type]
     return value
  else:
      raise Exception('hash type parameter not supported' )



def main():
    fields = {
        "raw": {"required": True, "type": "str"},
        "repo": {"required": True, "type": "str"}, 
        "version": {"required": True, "type": "str"},
        "option": {"required": True, "type": "str"},
        "address": {"required": True, "type": "str"},
        "port": {"required": True, "type": "str"},
        "hash_type": {"default": "sha1", "type": "str"}
        }
    module = AnsibleModule(argument_spec=fields)
    raw = module.params["raw"]
    repo = module.params["repo"]
    version = module.params["version"]
    option = module.params["option"]
    address = module.params["address"]
    port = module.params["port"]
    hash_type = module.params["hash_type"]
    result = get_checksum(raw,repo,option,version,address,hash_type)
    module.exit_json(msg=result)


if __name__ == '__main__':
    main()

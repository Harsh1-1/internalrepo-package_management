#!/usr/bin/python

import apt_inst
from debian import deb822
import os
from pprint import pprint
import json

package_dict = dict()

package_dir = '../sample_packages/'

#structue is like ['package_name'] = [{package_1_control_dict},{package_2_control_dict}]
for package in os.listdir(package_dir):
        #still need to fix error in the below statement, this try catch is because of this shit only
    try:
        control_data = apt_inst.DebFile(package_dir + package).control.extractdata('control')
        control_dict = deb822.Deb822(control_data.split("\n"))
        package_dict[ str(control_dict['Package']) ] = list()
        d = dict()
        d['Version'] = str(control_dict['Version'])
        d['Architecture'] = str(control_dict['Architecture'])
        d['Maintainer'] = str(control_dict['Maintainer'])
        d['Description'] = str(control_dict['Description'])
        package_dict[ str(control_dict['Package']) ].append(d)
    except Exception as e:
        continue
pprint(package_dict)
f = open('packages.json','w')
json.dump(package_dict,f)
f.close()

# print(package_dict['Python'])
# print(len(package_dict))
# print(len(os.listdir(package_dir)))

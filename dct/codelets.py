# ****************************************************************************#
# Copyright (c) 2022  Wandemberg Gibaut                                       #
# All rights reserved. This program and the accompanying materials            #
# are made available under the terms of the MIT License                       #
# which accompanies this distribution, and is available at                    #
# https://opensource.org/licenses/MIT                                         #
#                                                                             #
# Contributors:                                                               #
#      W. Gibaut                                                              #
#                                                                             #
# ****************************************************************************#

import json
import sys
import os
import time

class PythonCodelet:
    '''
    Base class for Codelets created in Python
        :param name: name of the codelet
        :param root_codelet_dir: path to the codelet directory
    '''
    def __init__(self, name=None, root_codelet_dir=None):
        if root_codelet_dir is None:
            os.chdir(os.path.dirname(__file__))
            root_codelet_dir = os.getcwd()
        self.root_codelet_dir = root_codelet_dir
        self.name = name
        self.fields = self.read_all_field()

    def read_field(self, field):
        with open(self.root_codelet_dir + '/fields.json', 'r') as json_data:
            jsonData = json.load(json_data)
            value = jsonData[field]
        return value
    
    def read_all_field(self):
        with open(self.root_codelet_dir + '/fields.json', 'r') as json_data:
            jsonData = json.load(json_data)
        return jsonData

    def write_all_field(self):
        with open(self.root_codelet_dir + '/fields.json', 'w+') as json_data:
            json.dump(self.fields, json_data)
            json_data.truncate()
    
    
    def change_field(self, field, value):
        self.fields[field] = value
        self.write_all_field()
        '''with open(self.root_codelet_dir + '/fields.json', 'r+') as json_data:
            jsonData = json.load(json_data)
            jsonData[field] = value
            # print(jsonData[field])

            json_data.seek(0)  # rewind
            json.dump(jsonData, json_data)
            json_data.truncate()'''

    def add_entry(self, field, data):
        with open(self.root_codelet_dir + '/fields.json', 'r+') as json_data:
            jsonData = json.load(json_data)
            vector = jsonData[field]
            vector.append(json.loads(data))
            jsonData[field] = vector

            json_data.seek(0)  # rewind
            json.dump(jsonData, json_data)
            json_data.truncate()

    def remove_entry(self, field, name):
        with open(self.root_codelet_dir + '/fields.json', 'r+') as json_data:
            jsonData = json.load(json_data)
            vector = jsonData[field]

            for i in vector:
                for k, v in i.items():
                    if v == name:
                        vector.remove(i)
                        return i

            jsonData[field] = vector
            # print(jsonData[field])

            json_data.seek(0)  # rewind
            json.dump(jsonData, json_data)
            json_data.truncate()

    def set_field_list(self, field, dataList):
        jsonList = []
        for dataString in dataList:
            jsonList.append(json.loads(dataString))

        with open(self.root_codelet_dir + '/fields.json', 'r+') as json_data:
            jsonData = json.load(json_data)
            jsonData[field] = jsonList
            # print(jsonData[field])

            json_data.seek(0)  # rewind
            json.dump(jsonData, json_data)
            json_data.truncate()

    @staticmethod
    def convert(self, string):
        li = list(string.split(";"))
        return li

    def run(self):
        while self.fields['enable'] == True:
            while self.fields['lock'] == False:
                activation = self.calculate_activation()
                self.proc(activation)
                time.sleep(float(self.fields['timestep']))
        '''while self.read_field('enable') == 'true':
            while self.read_field('lock') == 'false':
                activation = self.calculate_activation()
                self.proc(activation)
                time.sleep(float(self.read_field('timestep')))'''

        sys.exit()

    def calculate_activation(self):
        ########################################
        # Default Activation ##
        #print("default activation")
        return 0

    def proc(self, activation):
        ########################################
        # Default proc ##
        #print("default proc")
        pass

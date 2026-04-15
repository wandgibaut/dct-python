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
import requests
import socket
import redis
from pymongo import MongoClient
from bson import json_util
from dct import codelets
#from dct import parser
from dct import server
from dct import utils

__version__ = '0.1.0'
__author__ = 'Wandemberg Gibaut'


def get_memory_object(memory_name : str, ip_port : str, conn_type : str) -> list[dict]:
    '''
    Get a memory object given its name, ip/port and type
        :param memory_name: name of the memory object
        :param ip_port: ip/port of the memory object
        :param conn_type: type of the memory object
        :return: list of memory objects or None if error
        :rtype: list[dict]
    '''
    if conn_type == 'mongo':
        return get_mongo_memory(ip_port, memory_name)
    elif conn_type == 'redis':
        return get_redis_memory(ip_port, memory_name)
    elif conn_type == 'tcp':
        return get_tcp_memory(convert(":", ip_port)[0], convert(":", ip_port)[1], memory_name)
    elif conn_type == 'local':
        return get_local_memory(ip_port, memory_name)
    return None

#TODO: change TCP method
def set_memory_object(memory_name : str, ip_port : str, conn_type : str, field : str, value : object) -> int:
    '''
    Set a memory object given its name, ip/port, type, field and value
        :param memory_name: name of the memory object
        :param ip_port: ip/port of the memory object
        :param conn_type: type of the memory object
        :param field: field of the memory object
        :param value: value of the memory object
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    if conn_type == 'mongo':
        return set_mongo_memory(ip_port, memory_name, field, value)
    elif conn_type == 'redis':
        return set_redis_memory(ip_port, memory_name, field, value)
    elif conn_type == 'tcp':
        return set_tcp_memory(convert(":", ip_port)[0], convert(":", ip_port)[1], memory_name, field, value)
    elif conn_type == 'local':
        return set_local_memory(ip_port, memory_name, field, value)
    return -1


def get_memory_objects_by_name(root_codelet_dir : str, memory_name : str, inputOrOutput : str) -> list[dict]:
    '''
    Get a memory object given its name
        :param root_codelet_dir: root directory of the codelet
        :param memory_name: name of the memory object
        :param inputOrOutput: input or output memory object\
        :return: list of memory objects or None if error
        :rtype: list[dict]
    '''
    with open(root_codelet_dir + '/fields.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        vector = jsonData[inputOrOutput]
        answer = []
        for entry in vector:
            if entry['name'] == memory_name:
                answer.append(get_memory_object(memory_name, entry['ip/port'], entry['type']))
        if len(answer) != 0:
            return answer
        return None


def set_memory_objects_by_name(root_codelet_dir : str, memory_name : str, field : str, value : object, inputOrOutput : str) -> int:
    '''
    Set a memory object given its name, field and value
        :param root_codelet_dir: root directory of the codelet
        :param memory_name: name of the memory object
        :param field: field of the memory object
        :param value: value of the memory object
        :param inputOrOutput: input or output memory object
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    with open(root_codelet_dir + '/fields.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        vector = jsonData[inputOrOutput]
        for entry in vector:
            if entry['name'] == memory_name:
                set_memory_object(memory_name, entry['ip/port'], entry['type'], field, value)
        return 0


def get_memory_objects_by_group(root_codelet_dir : str, group : str, inputOrOutput : str) -> list[dict]:
    '''
    Get memory objects given their group
        :param root_codelet_dir: root directory of the codelet
        :param group: group of the memory object
        :param inputOrOutput: input or output memory object
        :return: list of memory objects or None if error
        :rtype: list[dict]
    '''
    with open(root_codelet_dir + '/fields.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        vector = jsonData[inputOrOutput]
        answer = []
        for entry in vector:
            if group in entry['group']:
                answer.append(get_memory_object(entry['name'], entry['ip/port'], entry['type']))
        if len(answer) != 0:
            return answer
        return None


def set_memory_objects_by_group(root_codelet_dir : str, group : str, field : str, value : object, inputOrOutput : str) -> int:
    '''
    Set memory objects given their group, field and value
        :param root_codelet_dir: root directory of the codelet
        :param group: group of the memory object
        :param field: field of the memory object
        :param value: value of the memory object
        :param inputOrOutput: input or output memory object
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    with open(root_codelet_dir + '/fields.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        vector = jsonData[inputOrOutput]
        for entry in vector:
            if group in entry['group']:
                set_memory_object(entry['name'], entry['ip/port'], entry['type'], field, value)
        return 0


def get_all_memory_objects(root_codelet_dir : str, inputOrOutput : str) -> list[dict]:
    '''
    Get all memory objects
        :param root_codelet_dir: root directory of the codelet
        :param inputOrOutput: input or output memory object
        :return: list of memory objects or None if error
        :rtype: list[dict]
    '''
    with open(root_codelet_dir + '/fields.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        vector = jsonData[inputOrOutput]
        answer = []
        for entry in vector:
            answer.append(get_memory_object(entry['name'], entry['ip/port'], entry['type']))
        if len(answer) != 0:
            return answer
        return None


def get_redis_memory(host_port : str, memory_name : str) -> dict:
    '''
    Get a redis memory object given its name and ip/port
        :param host_port: ip/port of the memory object
        :param memory_name: name of the memory object
        :return: memory object or None if error
        :rtype: dict
    '''
    url = host_port.split(':')
    host = url[0]
    port = url[1]
    try:
        client = redis.Redis(host=host, port=port)
        return json.loads(client.get(memory_name))
    except Exception as e:
        print(e)
        return None


def set_redis_memory(host_port : str, memory_name : str, field : str, value : object, full_memory : dict = None) -> int:
    '''
    Set a redis memory object given its name, ip/port, field and value
        :param host_port: ip/port of the memory object
        :param memory_name: name of the memory object
        :param field: field of the memory object
        :param value: value of the field
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    url = host_port.split(':')
    host = url[0]
    port = url[1]

    client = redis.Redis(host=host, port=port)

    if full_memory is not None:
        client.set(memory_name, json.dumps(full_memory))
        return 0

    
    try:
        mem = json.loads(client.get(memory_name))
    except:
        mem = {'name': memory_name,'ip/port': host_port,'type': 'redis', 'group': [],'I': None,'eval': 0.0}
        client.set(memory_name, json.dumps(mem))
    mem[field] = value
    client.set(memory_name, json.dumps(mem))
    return 0


def get_mongo_memory(host_port : str, memory_name : str) -> dict:
    '''
    Get a mongo memory object given its name and ip/port
        :param host_port: ip/port of the memory object
        :param memory_name: name of the memory object
        :return: memory object or None if error
        :rtype: dict
    '''
    client = MongoClient(host_port)
    try:
        base = client['database-raw-memory']
        collection = base[convert(":", memory_name)[0]]
        data = collection.find_one({'name': convert(":", memory_name)[1]})
        return json.loads(json_util.dumps(data))
    except Exception as e:
        print(e)
        return None


def set_mongo_memory(host_port : str, memory_name : str, field : str, value : object) -> int:
    '''
    Set a mongo memory object given its name, ip/port, field and value
        :param host_port: ip/port of the memory object
        :param memory_name: name of the memory object
        :param field: field of the memory object
        :param value: value of the field
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    client = MongoClient(host_port)
    base = client['database-raw-memory']
    collection = base[convert(":", memory_name)[0]]
    try:
        collection.update_one({'name': convert(":", memory_name)[1]}, {'$set': {field: value}})
    except:
        mem = {'name': convert(":", memory_name)[1],'ip/port': host_port,'type': 'mongo', 'group': [],'I': None,'eval': 0.0}
        mem[field] = value
        collection.insert_one(mem)
    return 0


def get_tcp_memory(host : str, port : str, memory_name : str) -> dict:
    '''
    Get a tcp memory object given its name, ip and port
        :param host: ip of the memory object
        :param port: port of the memory object
        :param memory_name: name of the memory object
        :return: memory object or None if error
        :rtype: dict
    '''
    response = requests.get(f'http://{host}:{port}/get_memory/{memory_name}')
    return response.json()


def set_tcp_memory(host : str, port : str, memory_name : str, field : str, value : object) -> requests.Response:
    '''
    Set a tcp memory object given its name, ip, port, field and value
        :param host: ip of the memory object
        :param port: port of the memory object
        :param memory_name: name of the memory object
        :param field: field of the memory object
        :param value: value of the field
        :return: response of the request
        :rtype: requests.Response
    '''
    response = requests.post(f'http://{host}:{port}/set_memory/', json={'memory_name': memory_name, 'field': field, 'value': value})
    return response


def get_local_memory(path : str, memory_name : str) -> dict:
    '''
    Get a local memory object given its name and path
        :param path: path of the memory object
        :param memory_name: name of the memory object
        :return: memory object or None if error
        :rtype: dict
    '''
    with open(path + '/' + memory_name + '.json', 'r+') as json_data:
        return json.load(json_data)


def set_local_memory(path : str, memory_name : str, field : str, value : object) -> int:
    '''
    Set a local memory object given its name, path, field and value
        :param path: path of the memory object
        :param memory_name: name of the memory object
        :param field: field of the memory object
        :param value: value of the field
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    with open(path + '/' + memory_name + '.json', 'r+') as json_data:
        jsonData = json.load(json_data)
        jsonData[field] = value
        # print(jsonData[field])

        json_data.seek(0)  # rewind
        json.dump(jsonData, json_data)
        json_data.truncate()
    return 0


#TODO: solve this issue
def add_memory_to_group(root_codelet_dir : str, memory_name : str, newGroup : str, inputOrOutput : str) -> int:
    '''
    Add a memory to a group
        :param root_codelet_dir: root directory of the codelet
        :param memory_name: name of the memory object
        :param newGroup: name of the group
        :param inputOrOutput: input or output
        :return: 0 if success, -1 if error
        :rtype: int
    '''
    memory_group = get_memory_objects_by_group(root_codelet_dir, memory_name, inputOrOutput)['group']
    memory_group.append(newGroup)
    set_memory_objects_by_name(root_codelet_dir, memory_name, 'group', memory_group, inputOrOutput)
    return 0


def get_node_info(host : str, port : str) -> dict:
    '''
    Get the node info
        :param host: ip of the node
        :param port: port of the node
        :return: node info
        :rtype: dict
    '''
    #data = 'info'
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
    #    sock.connect((host, int(port)))
    #    sock.sendall(bytes(data + "\n", "utf-8"))
        # Receive data from the server and shut down
    #    received = str(sock.recv(1024), "utf-8")
    #    print(received)
    #    try:
    #        answer = json.loads(received)
    #    except:
    #        answer = []
    #        raise Exception
    #    #return answer

    response = requests.get(f'http://{host}:{port}//get_node_info')
    return response.json()

def get_codelet_info(host : str, port : str, codelet_name : str) -> dict:
    '''
    Get the codelet info
        :param host: ip of the node
        :param port: port of the node
        :param codelet_name: name of the codelet
        :return: codelet info
        :rtype: dict
    '''
    #data = 'info_' + codelet_name
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
    #    sock.connect((host, int(port)))
    #    sock.sendall(bytes(data + "\n", "utf-8"))
        # Receive data from the server and shut down
    #    received = str(sock.recv(1024), "utf-8")
    #    print(received)
    #    try:
    #        answer = json.loads(received)
    #    except:
    #        answer = []
    #        raise Exception
    #    return answer

    response = requests.get(f'http://{host}:{port}//get_codelet_info/{codelet_name}')
    return response.json()

def convert(separator, string):
    li = list(string.split(separator))
    return li

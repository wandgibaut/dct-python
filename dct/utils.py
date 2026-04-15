# *****************************************************************************#
# Copyright (c) 2022  Wandemberg Gibaut                                       #
# All rights reserved. This program and the accompanying materials            #
# are made available under the terms of the MIT License                       #
# which accompanies this distribution, and is available at                    #
# https://opensource.org/licenses/MIT                                         #
#                                                                             #
# Contributors:                                                               #
#      W. Gibaut                                                              #
#                                                                             #
# *****************************************************************************#
from __future__ import annotations

import sys
import os
import getopt
import json
import shlex
import subprocess
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import time
from typing import Union

from dct.api import get_codelet_info as api_get_codelet_info, get_node_info as api_get_node_info

#TODO: add the possibility of including groups
def add_node_to_system(node_folder : str, ip_port_hostmode : str, new_node_name : str, node_params : dict, mount_options: str = ''):
    '''
    Adds a new node to the system
        :param node_folder: the folder of the node to be added
        :param ip_port_hostmode: the ip, port and hostmode of the node to be added
        :param new_node_name: the name of the node to be added
        :param node_params: the codelets, inputs and outputs of the node to be added. The format is:
        codelet1 ={
            'name': 'codelet_name',
            'inputs': [{'name': 'memory_name', 'type': 'type', 'ip/port': '127.0.0.1:9998', 'group':[]}],
            'outputs': [{'name': 'memory_name', 'type': 'type', 'ip/port': '127.0.0.1:9998', 'group':[]}]
        }
        node_params = {'codelets': [codelet1]}
    '''
    change_inputs_outputs_from_all_codelets(node_folder, node_params)

    print(node_folder + ' ' + ip_port_hostmode)
    # calls the add simple container script
    #subprocess.check_call(['./add_simple_container.sh', node_folder, ip_port_hostmode, new_node_name])

    docker_run_command = [
        'docker', 'run',
        '--name', new_node_name,
        '-d',
        '-it',
        '--network', 'host',
        *shlex.split(mount_options),
        '--env', 'ROOT_NODE_DIR=/home/node',
        'wandgibaut/python_codelet',
        '/bin/bash',
    ]
    subprocess.check_call(docker_run_command)
    time.sleep(2)
    subprocess.check_call(['docker', 'cp', f'{node_folder}/.', f'{new_node_name}:/home/node'])
    subprocess.check_call(['docker', 'exec', '-d', new_node_name, '/home/node/nodeMaster.sh', ip_port_hostmode])


def change_inputs_outputs_from_all_codelets(node_folder : str, node_params : dict):
    '''
    Changes the inputs and outputs of all codelets in the node_folder
        :param node_folder: the folder of the node to be added
        :param node_params: the codelets, inputs and outputs of the node to be added. The format is:
        codelet1 ={
            'name': 'codelet_name',
            'inputs': [{'name': 'memory_name', 'type': 'type', 'ip/port': '127.0.0.1:9998', 'group':[]}],
            'outputs': [{'name': 'memory_name', 'type': 'type', 'ip/port': '127.0.0.1:9998', 'group':[]}]
        }
        node_params = {'codelets': [codelet1]}
    '''
    codelets_to_add = node_params['codelets']
    for codelet in codelets_to_add:
        if codelet == '':
            continue
        #name_input_output = convert(' ', codelet)
        with open(node_folder + '/codelets/' + codelet['name'] + '/fields.json', 'r+') as json_data:
            codelet_info = json.load(json_data)
            new_inputs = []
            if len(codelet['inputs']) != 0:
                for input_mem in codelet['inputs']:
                    new_inputs.append(input_mem)

            codelet_info['inputs'] = new_inputs

            new_outputs = []
            if len(codelet['outputs']) != 0:
                for output_mem in codelet['outputs']:
                    new_outputs.append(output_mem)

            codelet_info['outputs'] = new_outputs

            # updates the fields.json
            json_data.seek(0)  # rewind
            json.dump(codelet_info, json_data)
            json_data.truncate()


def add_random_consumer(node_folder : str, ip_port_hostmode : str, number_of_feeders : int, list_of_memories_json : str):
    '''
    Adds a random consumer to the system
        :param node_folder: the folder of the node to be added
        :param ip_port_hostmode: the ip, port and hostmode of the node to be added
        :param number_of_feeders: the number of feeders to be added
        :param list_of_memories_json: the list of memories in the system
    '''

    with open(list_of_memories_json, 'r+') as json_data:
        memories_info = json.load(json_data)

        inputs = ''
        for codelet in os.listdir(node_folder + '/codelets'):
            inputs += codelet + ' '
            if number_of_feeders == '-1':
                choosen_infos = random.choices(memories_info, k=random.randrange(len(memories_info)))
            else:
                choosen_infos = random.choices(memories_info, k=int(number_of_feeders))

            if len(choosen_infos) != 0:
                for info in choosen_infos:
                    input_codelet = info['name'] + '@' + info['type'] + '@' + info['ip/port'] + ','
                    inputs += input_codelet
                inputs += ' '
                inputs = inputs.replace(', ', ' none; ')
            else:
                inputs += 'none none; '

        inputs += '$'
        inputs = inputs.replace('; $', '')

        print(inputs)
        add_node_to_system(node_folder, ip_port_hostmode, 'random_' + str(random.randint(0, 1000)), inputs)


def add_multiple_random_consumers(node_folder : str, ip_port_hostmode_list_json : str, number_of_feeders_array : list[Union[int, str]],
                                  list_of_memories_json : str, number_of_nodes : int):
    '''
    Adds multiple random consumers to the system
        :param node_folder: the folder of the node to be added
        :param ip_port_hostmode_list_json: the list of ips, ports and hostmodes of the nodes to be added
        :param number_of_feeders_array: the number of feeders to be added
        :param list_of_memories_json: the list of memories in the system
        :param number_of_nodes: the number of nodes to be added
    '''
    with open(ip_port_hostmode_list_json, 'r+') as json_list:
        ip_port_hostmode_list = json.load(json_list)
        if number_of_feeders_array[0] == '-1':
            for i in range(int(number_of_nodes)):
                add_random_consumer(node_folder, ip_port_hostmode_list[i], -1, list_of_memories_json)
        else:
            for i in range(int(number_of_nodes)):
                add_random_consumer(node_folder, ip_port_hostmode_list[i], number_of_feeders_array[i],
                                    list_of_memories_json)


# TODO: test
def add_multiple_scale_consumers(node_folder : str, ip_port_hostmode_list_json : str, number_of_feeders_array : list[Union[int, str]],
                                  list_of_memories_json : str, number_of_nodes : int):
    '''
    Adds multiple scale consumers to the system
        :param node_folder: the folder of the node to be added
        :param ip_port_hostmode_list_json: the list of ips, ports and hostmodes of the nodes to be added
        :param number_of_feeders_array: the number of feeders to be added
        :param list_of_memories_json: the list of memories in the system
        :param number_of_nodes: the number of nodes to be added
    '''
    with open(ip_port_hostmode_list_json, 'r+') as json_list:
        ip_port_hostmode_list = json.load(json_list)

        with open(list_of_memories_json, 'r+') as json_data:
            memories_info = json.load(json_data)
            ips= list(map(lambda datum: datum['ip/port'], memories_info))
            list_of_codelets = []
            for ip in ips:
                list_of_codelets.append(convert(":", ip))
            matrix = np.array(create_matrix(get_all_codelets_infos(list_of_codelets)))
            number_of_connections = matrix.sum(axis=1, dtype='float')
            total_number_of_connections = matrix.sum(dtype='float')

            density = number_of_connections/total_number_of_connections

            draw = np.random.choice(ips, 10, p=density)
            print(draw)

            for i in range(int(number_of_nodes)):
                input_codelets_ips = [draw[i]]

                add_random_consumer(node_folder, ip_port_hostmode_list[i], number_of_feeders_array[i],
                                    list_of_memories_json)

        #TODO: continuar


def remove_docker_node_from_system(node_name : str):
    '''
    Removes a docker node from the system
        :param node_name: the name of the node to be removed
    '''
    # calls the add simple container script
    subprocess.check_call(['docker', 'stop', node_name])


def get_codelet_info(host : str, port : str, codelet_name : str) -> dict:
    '''
    Gets the info of a codelet
        :param host: the host of the codelet
        :param port: the port of the codelet
        :param codelet_name: the name of the codelet
        :return: the info of the codelet
        :rtype: dict
    '''
    return api_get_codelet_info(host, port, codelet_name)


def get_all_codelets_infos(list_of_codelets : list[list[str]]) -> list[dict]:
    '''
    Gets the info of all codelets
        :param list_of_codelets: the list of codelets with the host, port and name
        :return: the info of all codelets
        :rtype: list[dict]
    '''
    answer = []
    for codelet in list_of_codelets:
        answer.append(get_codelet_info(codelet[0], codelet[1], codelet[2]))

    return answer


def get_node_info(host : str, port : str) -> dict:
    '''
    Gets the info of a node
        :param host: the host of the node
        :param port: the port of the node
        :return: the info of the node
        :rtype: dict
    '''
    return api_get_node_info(host, port)


def get_all_nodes_infos(list_of_ips : list[str]) -> list[dict]:
    '''
    Gets the info of all nodes
        :param list_of_ips: the list of ips of the nodes
        :return: the info of all nodes
        :rtype: list[dict]
    '''
    answer = []
    for node in list_of_ips:
        entry = {'node_name': node, 'info': get_node_info(convert(':', node)[0], convert(':', node)[1])}
        answer.append(entry)
    return answer


def create_matrix(list_of_nodes_infos : list[dict]) -> list[list[int]]:
    '''
    Creates a matrix with the connections between nodes
        :param list_of_nodes_infos: the list of nodes with their info
        :return: the matrix with the connections between nodes
        :rtype: list[list[int]]
    '''
    # empty matrix
    matrix = []
    for i in range(len(list_of_nodes_infos)):
        row = []
        for j in range(len(list_of_nodes_infos)):
            row.append(0)
        matrix.append(row)
    # fill matrix
    for i in range(len(list_of_nodes_infos)):
        node_i = list_of_nodes_infos[i]
        inputs_i = node_i['info']['input_ips']
        outputs_i = node_i['info']['output_ips']
        for j in range(len(list_of_nodes_infos)):
            for k in range(len(inputs_i)):
                if inputs_i[k] in list_of_nodes_infos[j]['info']['output_ips']:
                    matrix[i][j] = 1
                if inputs_i[k] == list_of_nodes_infos[j]['node_name']:
                    matrix[i][j] = 1

            for k in range(len(outputs_i)):
                if outputs_i[k] in list_of_nodes_infos[j]['info']['input_ips']:
                    matrix[i][j] = 1
                if outputs_i[k] == list_of_nodes_infos[j]['node_name']:
                    matrix[i][j] = 1

            # se inputs == outputs, marque uma conexão
    return matrix


def draw_network(list_of_ips : list[str], graph_name : str):
    '''
    Draws the network
        :param list_of_ips: the list of ips of the nodes
        :param graph_name: the name of the graph
    '''
    matrix = create_matrix(get_all_nodes_infos(list_of_ips))

    print(matrix)
    # g = nx.from_numpy_matrix(np.array(matrix))
    g = nx.from_numpy_matrix(np.array(matrix), create_using=nx.DiGraph)
    f = plt.figure()
    
    node_color = []
    for node in nx.nodes(g):
        node_color.append(g.degree(node))

    # nx.draw(g, ax=f.add_subplot(111), with_labels=True)
    nx.draw_shell(g, ax=f.add_subplot(111), with_labels=True, node_size=200, node_color=node_color, cmap=plt.cm.Blues)
    f.savefig(graph_name)


def convert(separator, string):
    li = list(string.split(separator))
    return li


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:f:e:c:i:s:l:L:n:C:", ["help=", "option=", "node-folder=",
                                                                           "ip-port=", "node-name=",
                                                                           "connections-info=", "sources=",
                                                                           "ip-port-hostmode-list-json=",
                                                                           "list-of-memories-json=",
                                                                           "number-of-nodes=", "list-of-nodes="])
    except getopt.GetoptError:
        print('call with -h or --help to see options')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('options: -o --option, -f --node-folder, -e --ip-port, -c --node-name, -i --connections-info, \n'
                  '-s --sources, -l --ip-port-hostmode-list-json, -L --list-of-memories-json, -n --number-of-nodes, \n'
                  '-C --list-of-nodes \n \n'
                  '### example usages ### \n'
                  'to insert a random node that only consumes: \n'
                  'python3 utils.py --option random -f node_test --ip-port 127.0.0.1:9996 -s -1 -L '
                  'list_of_memories.json \n'
                  'to insert a full defined node: \n'
                  'python3 utils.py --option specific -f node_test -e 127.0.0.1:9995 --node-name test_node_1 -i '
                  '\'behavioral sensory-memory@tcp@127.0.0.1:9998 motor-memory@local@home/codelets/behavioral/memories;'
                  ' motor motor-memory@local@home/codelets/behavioral/memories none\' \n'
                  'to add multiple random nodes: \n'
                  'python3 utils.py --option multiple-random -f node_test -l open_ports.json -s -1 -L '
                  'list_of_memories.json -n 5 \n'
                  'to kill a node: \n'
                  'python3 utils.py --option remove -c random_286\n'
                  'to draw a image representing the network: \n'
                  'python3 utils.py --option draw-network -C 127.0.0.1:9998,127.0.0.1:9997,127.0.0.1:9996')
            sys.exit()
        elif opt in ('-o', '--option'):
            option = arg
        elif opt in ('-f', '--node-folder'):
            node_folder = arg
        elif opt in ('-e', '--ip-port'):
            ip_port_hostmode = arg
        elif opt in ('-c', '--node-name'):
            new_node_name = arg
            node_name = arg
        elif opt in ('-i', '--connections-info'):
            input_codelets_ips = arg.split(',')
        elif opt in ('-s', '--sources'):
            number_of_feeders_array = arg.split(',')
            if len(number_of_feeders_array) == 1:
                number_of_feeders = number_of_feeders_array[0]
        elif opt in ('-l', '--ip-port-hostmode-list-json'):
            ip_port_hostmode_list_json = arg
        elif opt in ('-L', '--list-of-memories-json'):
            list_of_memories_json = arg
        elif opt in ('-n', '--number-of-nodes'):
            number_of_nodes = arg
        elif opt in ('-C', '--list-of-nodes'):
            list_of_nodes = arg.split(',')

    try:
        if option == 'random':
            add_random_consumer(node_folder, ip_port_hostmode, number_of_feeders, list_of_memories_json)

        elif option == 'specific':
            add_node_to_system(node_folder, ip_port_hostmode, new_node_name, input_codelets_ips[0])

        elif option == 'scale':
            add_multiple_scale_consumers(node_folder, ip_port_hostmode_list_json, number_of_feeders_array,
                                         list_of_memories_json, number_of_nodes)

        elif option == 'multiple-random':
            add_multiple_random_consumers(node_folder, ip_port_hostmode_list_json, number_of_feeders_array,
                                          list_of_memories_json, number_of_nodes)

        elif option == 'remove':
            remove_docker_node_from_system(node_name)

        elif option == 'draw-network':
            draw_network(list_of_nodes, "graph.png")
    except:
        print('Error! Call with -h or --help to see options')

    sys.exit()

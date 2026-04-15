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

import os
import sys
import json
import os
import glob
import configparser
import requests
from flask import Flask, request, Response
import dct


root_node_dir = os.getenv('ROOT_NODE_DIR')
death_threshold = 3
death_votes = 0

app = Flask(__name__)



@app.route('/')
def home():
    return "API."


@app.route('/get_memory/<memory_name>')
def get_memory(memory_name : str) -> Response:
    '''
    API routine to return a memory object
        :param memory_name: name of the memory object
        :return: memory object
        :rtype: Response
    '''
    for filename in glob.iglob(root_node_dir + '/**', recursive=True):
        if filename.__contains__('fields.json'):
            with open(filename, 'r+') as json_data:
                jsonData = json.load(json_data)
                for inputOrOutput in ['inputs', 'outputs']:
                    vector = jsonData[inputOrOutput]
                    answer = []
                    for entry in vector:
                        if entry['name'] == memory_name:
                            #file_memory = entry['file']
                            answer.append(dct.get_memory_object(memory_name, entry['ip/port'], entry['type']))
                    if len(answer) != 0:
                        return answer
    return Response(status=404, headers={})


@app.route('/set_memory/', methods=['POST'])
def set_memory():
    request_data = json.dumps(json.loads(request.get_json()))
    memory_name = request_data['memory_name']
    field = request_data['field']
    value = request_data['value']

    for filename in glob.iglob(root_node_dir + '/**', recursive=True):
        if filename.__contains__('fields.json'):
            with open(filename, 'r+') as json_data:
                jsonData = json.load(json_data)
                for inputOrOutput in ['inputs', 'outputs']:
                    vector = jsonData[inputOrOutput]
                    for entry in vector:
                        if entry['name'] == memory_name:
                            #file_memory = entry['file']
                            dct.set_memory_object(memory_name, entry['ip/port'], entry['type'], field, value)
                            return Response(status=200, headers={})
    return Response(status=404, headers={})


@app.route('/get_idea/<idea_name>')
def get_idea(idea_name : str) -> Response:
    '''
    API routine to return a memory object
        :param idea_name: name of the memory object
        :return: memory object
        :rtype: Response
    '''
    
    url = args[0].split(':')
    redis_url = f'{url[0]}:{str(int(url[1]) + 1)}'
    return json.dumps(dct.get_redis_memory(redis_url, idea_name))  # dict
    

@app.route('/set_idea/', methods=['POST'])
def set_idea():
    #print(request.get_json())
    #json.loads(request.get_data())
    if type(request.get_json()) == dict:
        request_data = request.get_json()
    else:
        request_data = json.loads(request.get_json())

    url = args[0].split(':')
    redis_url = f'{url[0]}:{str(int(url[1]) + 1)}'

    if 'full_idea' in request_data:
        full_idea = validate_idea(request_data['full_idea'])
        if full_idea is None:
            return Response(status=400, headers={})

        idea_name = request_data['full_idea']['name']
        dct.set_redis_memory(redis_url, idea_name, None, None, full_memory=full_idea)
    
    else:
        idea_name = request_data['name']
        field = request_data['field']
        value = request_data['value']
        dct.set_redis_memory(redis_url, idea_name, field, value)
    return Response(status=200, headers={})

@app.route('/get_codelet_info/<codelet_name>')
def get_codelet_info(codelet_name):
    file_fields = None
    for filename in glob.iglob(root_node_dir + '/**', recursive=True):
        if filename.__contains__(codelet_name + '/fields.json'):
            file_fields = filename
    if file_fields is None:
        return Response(status=404, headers={})
    with open(file_fields, 'r+') as json_data:
        fields = json.dumps(json.load(json_data))
        return fields

@app.route('/get_node_info')
def get_node_info():
    print(root_node_dir )
    number_of_codelets = 0
    input_ips = []
    output_ips = []
    for filename in glob.iglob(root_node_dir + '/**', recursive=True):
        if filename.__contains__('fields.json'):
            number_of_codelets += 1
            with open(filename, 'r+') as json_data:
                fields = json.load(json_data)
                add_inputs = [item['ip/port'] for item in fields['inputs']]
                add_outputs = [item['ip/port'] for item in fields['outputs']]
                for entry in add_inputs:
                    if entry not in input_ips:
                        input_ips.append(entry)
                for entry in add_outputs:
                    if entry not in output_ips:
                        output_ips.append(entry)

    answer = {'number_of_codelets': number_of_codelets, 'input_ips': input_ips, 'output_ips': output_ips}
    return json.dumps(answer)

@staticmethod
def convert(string):
    li = list(string.split("_"))
    return li

def read_param():
    config = configparser.ConfigParser()
    config.read(root_node_dir + '/param.ini', encoding='utf-8')
    return config

def set_param(section, field, value):
    config = read_param()
    config.set(section, field, value)
    with open(root_node_dir + '/param.ini', 'w') as configfile:
        config.write(configfile)

def remove_param(section, field):
    config = read_param()
    config.remove_option(section, field)
    with open(root_node_dir + '/param.ini', 'w') as configfile:
        config.write(configfile)


@app.route('/kill_codelet/<codelet_name>')
def kill_codelet(codelet_name):
    remove_param('active_codelets', codelet_name)
    return 'codelet will be stopped soon!'

@app.route('/run_codelet/<codelet_name>')
def run_codelet(codelet_name):
    config = read_param()
    if config.has_option('internal_codelets', codelet_name):
        set_param('active_codelets', codelet_name, codelet_name)
    return 'codelet will run soon!'

@app.route('/configure_death/')
def config_death():
    global death_threshold
    global death_votes
    config = read_param()
    death_threshold = int(config.get('signals', 'death_threshold'))
    death_votes = 0
    return Response(status=200, headers={})


#TODO: change url
@app.route('/vote_kill/', methods=['POST'])
def vote_kill():
    request_data = json.loads(request.get_json())
    url = request_data['url']
    
    response = requests.post(url + '/die', json={'voter_url': '2000'})
    print(response.json()) # a string confirming the vote
    return Response(status=200, headers={})


@app.route('/die/', methods=['POST'])
def listen_death_democracy():
    request_data = json.loads(request.get_json())
    voter_url = request_data['voter_url']

    if not hasattr('death_threshold'):
        config_death()

    config = read_param()
    for i in range(death_threshold):
        if config.has_option('signals', 'voter_' + str(i)):
            if config.get('signals', 'voter_' + str(i)) == voter_url:
                return 'vote already listened!'

    set_param('signals', 'voter_' + str(death_votes), voter_url)
    death_votes += 1

    if death_votes >= death_threshold:
        set_param('signals', 'suicide_note', 'true')
        return 'node will die!'

    return 'vote computed!'


#TODO: implement auth
@app.route('/die_now/')
def listen_death_authority():
    set_param('signals', 'suicide_note', 'true')
    return Response(status=200, headers={})

# TODO: implement this method
def listen_internal_codelet():
    return 0

def split(string): 
    li = list(string.split(":")) 
    return li 

def validate_idea(idea : dict) -> dict:
    idea_fields = set(['id', 'name', 'l', 'category', 'scope', 'value'])

    if idea_fields.issubset(idea.keys()):
        return idea
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    HOST = split(args[0])[0]
    PORT = int(split(args[0])[1])
    app.run(debug=True, host=HOST, port=PORT)
    #app.run(debug=True, host='127.0.0.1', port=5020)
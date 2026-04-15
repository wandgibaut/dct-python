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

from __future__ import annotations

import json
import os
import sys
import glob
import configparser
from collections.abc import Iterator
from typing import Any, Optional, Union
import requests
from flask import Flask, request, Response

from dct.api import get_memory_object, get_redis_memory, set_memory_object, set_redis_memory


root_node_dir = os.getenv('ROOT_NODE_DIR', os.getcwd())
death_threshold = 3
death_votes = 0

app = Flask(__name__)


def _iter_fields_files() -> Iterator[str]:
    return glob.iglob(os.path.join(root_node_dir, '**', 'fields.json'), recursive=True)


def _request_json() -> dict[str, Any]:
    request_data = request.get_json()
    if isinstance(request_data, str):
        request_data = json.loads(request_data)
    if not isinstance(request_data, dict):
        raise ValueError("JSON body must be an object")
    return request_data


def _redis_url_from_request() -> str:
    host, port = request.host.rsplit(':', 1)
    return f'{host}:{int(port) + 1}'


@app.route('/')
def home() -> str:
    return "API."


@app.route('/get_memory/<memory_name>')
def get_memory(memory_name: str) -> Union[list[dict[str, Any]], Response]:
    '''
    API routine to return a memory object
        :param memory_name: name of the memory object
        :return: memory object
        :rtype: Response
    '''
    for filename in _iter_fields_files():
        with open(filename, encoding='utf-8') as json_data:
            json_data_contents = json.load(json_data)
            for input_or_output in ['inputs', 'outputs']:
                vector = json_data_contents[input_or_output]
                answer = []
                for entry in vector:
                    if entry['name'] == memory_name:
                        answer.append(get_memory_object(memory_name, entry['ip/port'], entry['type']))
                if answer:
                    return answer
    return Response(status=404, headers={})


@app.route('/set_memory/', methods=['POST'])
def set_memory() -> Response:
    request_data = _request_json()
    memory_name = request_data['memory_name']
    field = request_data['field']
    value = request_data['value']

    for filename in _iter_fields_files():
        with open(filename, encoding='utf-8') as json_data:
            json_data_contents = json.load(json_data)
            for input_or_output in ['inputs', 'outputs']:
                vector = json_data_contents[input_or_output]
                for entry in vector:
                    if entry['name'] == memory_name:
                        set_memory_object(memory_name, entry['ip/port'], entry['type'], field, value)
                        return Response(status=200, headers={})
    return Response(status=404, headers={})


@app.route('/get_idea/<idea_name>')
def get_idea(idea_name: str) -> str:
    '''
    API routine to return a memory object
        :param idea_name: name of the memory object
        :return: memory object
        :rtype: Response
    '''
    
    redis_url = _redis_url_from_request()
    return json.dumps(get_redis_memory(redis_url, idea_name))  # dict
    

@app.route('/set_idea/', methods=['POST'])
def set_idea() -> Response:
    request_data = _request_json()
    redis_url = _redis_url_from_request()

    if 'full_idea' in request_data:
        full_idea = validate_idea(request_data['full_idea'])
        if full_idea is None:
            return Response(status=400, headers={})

        idea_name = request_data['full_idea']['name']
        set_redis_memory(redis_url, idea_name, None, None, full_memory=full_idea)
    
    else:
        idea_name = request_data['name']
        field = request_data['field']
        value = request_data['value']
        set_redis_memory(redis_url, idea_name, field, value)
    return Response(status=200, headers={})

@app.route('/get_codelet_info/<codelet_name>')
def get_codelet_info(codelet_name: str) -> Union[str, Response]:
    file_fields = None
    for filename in _iter_fields_files():
        if filename.endswith(os.path.join(codelet_name, 'fields.json')):
            file_fields = filename
    if file_fields is None:
        return Response(status=404, headers={})
    with open(file_fields, encoding='utf-8') as json_data:
        fields = json.dumps(json.load(json_data))
        return fields

@app.route('/get_node_info')
def get_node_info() -> str:
    number_of_codelets = 0
    input_ips = []
    output_ips = []
    for filename in _iter_fields_files():
        number_of_codelets += 1
        with open(filename, encoding='utf-8') as json_data:
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

def convert(string: str) -> list[str]:
    return string.split("_")

def read_param() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(os.path.join(root_node_dir, 'param.ini'), encoding='utf-8')
    return config

def set_param(section: str, field: str, value: str) -> None:
    config = read_param()
    config.set(section, field, value)
    with open(os.path.join(root_node_dir, 'param.ini'), 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def remove_param(section: str, field: str) -> None:
    config = read_param()
    config.remove_option(section, field)
    with open(os.path.join(root_node_dir, 'param.ini'), 'w', encoding='utf-8') as configfile:
        config.write(configfile)


@app.route('/kill_codelet/<codelet_name>')
def kill_codelet(codelet_name: str) -> str:
    remove_param('active_codelets', codelet_name)
    return 'codelet will be stopped soon!'

@app.route('/run_codelet/<codelet_name>')
def run_codelet(codelet_name: str) -> str:
    config = read_param()
    if config.has_option('internal_codelets', codelet_name):
        set_param('active_codelets', codelet_name, codelet_name)
    return 'codelet will run soon!'

@app.route('/configure_death/')
def config_death() -> Response:
    global death_threshold
    global death_votes
    config = read_param()
    death_threshold = int(config.get('signals', 'death_threshold'))
    death_votes = 0
    return Response(status=200, headers={})


#TODO: change url
@app.route('/vote_kill/', methods=['POST'])
def vote_kill() -> Response:
    request_data = _request_json()
    url = request_data['url']
    
    response = requests.post(url + '/die', json={'voter_url': '2000'})
    print(response.json()) # a string confirming the vote
    return Response(status=200, headers={})


@app.route('/die/', methods=['POST'])
def listen_death_democracy() -> str:
    global death_votes
    request_data = _request_json()
    voter_url = request_data['voter_url']

    if death_threshold <= 0:
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
def listen_death_authority() -> Response:
    set_param('signals', 'suicide_note', 'true')
    return Response(status=200, headers={})

# TODO: implement this method
def listen_internal_codelet() -> int:
    return 0

def split(string: str) -> list[str]:
    return string.split(":")

def validate_idea(idea: dict[str, Any]) -> Optional[dict[str, Any]]:
    idea_fields = {'id', 'name', 'l', 'category', 'scope', 'value'}

    if idea_fields.issubset(idea.keys()):
        return idea
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    HOST = split(args[0])[0]
    PORT = int(split(args[0])[1])
    app.run(debug=True, host=HOST, port=PORT)
    #app.run(debug=True, host='127.0.0.1', port=5020)

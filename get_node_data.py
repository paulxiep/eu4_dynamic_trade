import logging
import os

import yaml

from get_save_data import get_save_data
from util import *

with open('settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)
game_folder = settings['file_path']['game_folder']
node_data_folder = settings['file_path']['node_data_folder']


def find_close_bracket(string):
    open_brackets = 0
    i = 1
    for character in string[1:]:
        if character == '{':
            open_brackets += 1
        elif character == '}':
            open_brackets -= 1
        if open_brackets < 0:
            return i + 1
        else:
            i += 1


def load_node_data(node_data_text):
    def get_data(data):
        def get_name(outgoing):
            return outgoing[6: outgoing.find('\n') - 1]

        def get_path(outgoing):
            return outgoing.split('path={\n\t\t\t')[1].split('\n')[0].split(' ')[:-1]

        def get_members(members):
            return members.split('\n')[0].split(' ')[:-1]

        def get_location(location):
            return location.split('\n')[0]

        def get_control(outgoing):
            return outgoing.split('control={\n\t\t\t')[1].split('\n')[0].split(' ')[:-1]

        return list(map(get_name, data.split('outgoing={\n\t\t')[1:])), \
               list(map(get_path, data.split('outgoing={\n\t\t')[1:])), \
               data.find('inland') >= 0, \
               list(map(get_members, data.split('members={\n\t\t')[1:])), \
               list(map(get_location, data.split('location=')[1:])), \
               list(map(get_control, data.split('outgoing={\n\t\t')[1:]))

    def map_ids(node_ids):
        def map_id(v):
            return {'location': v[4], 'inland': v[2],
                    'outgoing_nodes': list(map(lambda x: str(node_ids[x]), v[0])),
                    'outgoing_paths': v[1],
                    'outgoing_control': v[5],
                    'members': v[3][0]
                    }

        return map_id

    nodes = {}
    node_ids = {}
    next_pos = node_data_text.find('{')
    while next_pos >= 0:
        node_name = node_data_text[:next_pos - 1]
        node_data_text = node_data_text[next_pos + 1:]
        close_pos = find_close_bracket(node_data_text)
        data = node_data_text[: close_pos]
        nodes[node_name] = get_data(data)
        node_ids[node_name] = node_name
        node_data_text = node_data_text[close_pos + 1:]
        next_pos = node_data_text.find('{')
    out = {str(k): map_ids(node_ids)(v) for k, v in nodes.items()}
    incoming_dict = {node: [] for node in out.keys()}
    incoming_path_dict = {node: [] for node in out.keys()}
    incoming_control_dict = {node: [] for node in out.keys()}
    for k, v in out.items():
        for node in v['outgoing_nodes']:
            incoming_dict[node].append(str(k))
            incoming_path_dict[node].append(
                list(flist(out[k]['outgoing_paths'][out[k]['outgoing_nodes'].index(node)]).copy().reverse()))
            incoming_control_dict[node].append(
                list(clist(out[k]['outgoing_control'][out[k]['outgoing_nodes'].index(node)]).copy().reverse()))
    logging.info('node data extracted')
    return {k: {'incoming_nodes': incoming_dict[k], 'incoming_paths': incoming_path_dict[k],
                'incoming_control': incoming_control_dict[k], **out[k]} for k in out.keys()}


def prepare_node_data(node_data):
    def accumulate_province_data(member, data):
        try:
            return float(province_data[member][data])
        except:
            return reduce(float.__add__, map(lambda x: float(province_data[x][data]), member.split('\t')))

    def accumulate_quadratic_province_data(member, data):
        try:
            return float(province_data[member][data]) ** 2
        except:
            return reduce(float.__add__, map(lambda x: float(province_data[x][data]) ** 2, member.split('\t')))

    province_data, countries = get_save_data()

    for v in node_data.values():
        v['node_connections'] = tlist(zip((v['incoming_nodes'] + v['outgoing_nodes']),
                                          list(map(lambda x: tuple(x), (v['incoming_paths'] + v['outgoing_paths']))),
                                          list(map(lambda x: tuple(x),
                                                   (v['incoming_control'] + v['outgoing_control'])))))
        for data in ['trade_power', 'tax', 'production', 'manpower', 'development']:
            v[data] = reduce(float.__add__, [accumulate_province_data(member, data) for member in v['members']])
        for data in ['trade_power', 'tax', 'production', 'manpower', 'development']:
            v[f'quadratic_{data}'] = reduce(float.__add__,
                                            [accumulate_quadratic_province_data(member, data) for member in
                                             v['members']])

    logging.info('node data prepared')
    return node_data, countries


def get_node_data():
    with open(os.path.join(node_data_folder, '00_tradenodes.txt'), 'r') as f:
        node_data_text = f.read()
    return prepare_node_data(load_node_data(node_data_text))

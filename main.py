import json
import operator
from functools import reduce
import os
import yaml
import re
from random import random
import shutil
from util import *
from get_save_data import get_save_data
from get_node_data import get_node_data

with open('settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)
all_mod_folder = settings['file_path']['all_mod_folder']
mod_path = settings['file_path']['mod_path']
node_data_path = settings['file_path']['node_data_path']
N_END_NODES = settings['flow_rules']['N_END_NODES']
FLOW_POWER_RULES = settings['flow_rules']['FLOW_POWER_RULES']
END_NODE_RESTRICTION = settings['flow_rules']['END_NODE_RESTRICTION']
RELOAD_SAVE_DATA = settings['RELOAD_SAVE_DATA']
# N_END_NODES = 3
# all_mod_folder = '/Users/paulx/Documents/Paradox Interactive/Europa Universalis IV/mod'
# mod_path = '/Users/paulx/Documents/Paradox Interactive/Europa Universalis IV/mod/dynamic_trade'
# node_data_path = 'common/tradenodes'
# FLOW_POWER_RULES = ['country_development', 'total_development', 'total_provincial_trade_power']
# END_NODE_RESTRICTION = 'restricted'
# RELOAD_SAVE_DATA = False

def rank_nodes_by_countries(countries, node_data):
    all_nodes = {}
    order = 1
    for value_pair in countries.values():
        if value_pair[1] is not None:
            try:
                country_node = list(filter(lambda x: value_pair[1] in x[1],
                                    [(key, value['members']) for key, value in node_data.items()]))[0][0]
                if country_node not in all_nodes.keys():
                    all_nodes[country_node] = order
                    order += 1
            except:
                print(value_pair)
    return all_nodes


def make_outgoing_restricted(node_data, node_rank, end_nodes):
    def min_with_index(iterator):
        min_index, min_value = min(enumerate(iterator), key=operator.itemgetter(1))
        return (N_END_NODES - min_index) + (20 - min_value) * 1000
    distance = 1
    nodes_at_distance = [[end_node] for end_node in end_nodes]
    for i, end_node in enumerate(end_nodes):
        node_data[end_node]['distance'] = [0 if j==i else 1 for j in range(N_END_NODES)]
        node_data[end_node]['outgoing'] = []
    all_nodes = [[end_node] for end_node in end_nodes]
    # all_nodes = [[] for _ in range(N_END_NODES)]
    while any([len(nodes_at_distance[i]) > 0 for i in range(N_END_NODES)]):
        for i in range(N_END_NODES):
            print(distance, nodes_at_distance[i])
            new_nodes_at_distance = []
            for node in nodes_at_distance[i]:
                for connection in node_data[node]['node_connections']:
                    if node_data[connection[0]].get('distance', None) is None:
                        node_data[connection[0]]['distance'] = [None for _ in range(N_END_NODES)]
                    if isinstance(node_data[connection[0]]['distance'], list) and node_data[connection[0]]['distance'][
                        i] is None:
                        node_data[connection[0]]['distance'][i] = distance
                    if connection[0] not in all_nodes[i]:
                        new_nodes_at_distance.append(connection[0])
                        all_nodes[i].append(connection[0])
                    if ((node_data[connection[0]]['distance'][i] > node_data[node]['distance'][i] \
                         and not any([node_data[connection[0]]['distance'][j] is not None \
                                      and node_data[connection[0]]['distance'][j] <
                                      node_data[connection[0]]['distance'][i] for j in range(0, i)])) \
                        or \
                        (node_data[connection[0]]['distance'][i] == node_data[node]['distance'][i] and
                         node_pull(node_data, node_rank)(connection[0], node))\
                        and not any([node_data[connection[0]]['distance'][j] is not None \
                                     and node_data[connection[0]]['distance'][j] < node_data[connection[0]]['distance'][
                                         i] for j in range(0, i)])) \
                            and node_data[node]['node_connections'][
                        node_data[node]['node_connections'].index(connection[0])] not in node_data[node].get('outgoing',
                                                                                                             []):

                        node_data[connection[0]]['outgoing'] = node_data[connection[0]].get('outgoing', []) + [
                            node_data[connection[0]]['node_connections'][
                                node_data[connection[0]]['node_connections'].index(node)]]
                        print(f'{connection[0]}->{node}')
            nodes_at_distance[i] = new_nodes_at_distance.copy()
        distance += 1
    for v in node_data.values():
        v.pop('node_connections')
        v.pop('outgoing_nodes')
        v.pop('outgoing_paths')
        v.pop('outgoing_control')
        v.pop('incoming_nodes')
        v.pop('incoming_paths')
        v.pop('incoming_control')
    return dict(sorted(node_data.items(), key=lambda x: 1000000000 * min_with_index([(x[1]['distance'][i]) for i in range(N_END_NODES)]) \
                                + node_score(node_data, node_rank)(x[0])))

def make_outgoing_unrestricted(node_data, node_rank, end_nodes):
    def make_node_outgoing(node):
        node_connections = node_data[node]['node_connections']
        outgoings = []
        for node_connection in node_connections:
            if node_pull(node_data, node_rank)(node, node_connection[0]):
                outgoings.append(node_connection)
        return outgoings
    for k, v in node_data.items():
        v['outgoing'] = make_node_outgoing(k)
    for v in node_data.values():
        v.pop('node_connections')
        v.pop('outgoing_nodes')
        v.pop('outgoing_paths')
        v.pop('outgoing_control')
        v.pop('incoming_nodes')
        v.pop('incoming_paths')
        v.pop('incoming_control')

    return dict(sorted(node_data.items(), key=lambda x: node_score(node_data, node_rank)(x[0])))

def node_score(node_data, node_rank):
    def get_score(node):
        score = 0
        for i, flow_power_rule in enumerate(FLOW_POWER_RULES):
            if flow_power_rule == 'country_development':
                score += (1000**(len(FLOW_POWER_RULES)-1-i)) * (1000 - node_rank.get(node, 1000))
            if flow_power_rule == 'total_development':
                score += (1000**(len(FLOW_POWER_RULES)-1-i)) * node_data[node]['tax'] + node_data[node]['production'] + node_data[node]['manpower']
            if flow_power_rule == 'total_trade_power':
                score += (1000**(len(FLOW_POWER_RULES)-1-i)) * node_data[node]['trade_power']
        return score
    return get_score

def node_pull(node_data, node_rank):
    def compare_nodes(first, second):
        for flow_power_rule in FLOW_POWER_RULES:
            if flow_power_rule == 'country_development':
                if node_rank.get(first, 1000) != node_rank.get(second, 1000):
                    return node_rank.get(first, 1000) > node_rank.get(second, 1000)
            if flow_power_rule == 'total_development':
                first_dev = node_data[first]['tax'] + node_data[first]['production'] + node_data[first]['manpower']
                second_dev = node_data[second]['tax'] + node_data[second]['production'] + node_data[second]['manpower']
                if first_dev != second_dev:
                    return first_dev < second_dev
            if flow_power_rule == 'total_provincial_trade_power':
                if node_data[first]['trade_power'] != node_data[second]['trade_power']:
                    return node_data[first]['trade_power'] < node_data[second]['trade_power']
        return random() < 0.5
    return compare_nodes

def make_outgoing(restricted='restricted'):
    if restricted == 'restricted':
        return make_outgoing_restricted
    if restricted == 'unrestricted':
        return make_outgoing_unrestricted

def gen_nodes_text(node_data):
    def gen_node_text(k, v):
        out = f'{k}=' + '{\n\tlocation=' + v['location'][0] + '\n\tinland=yes' * v['inland'] + '\n\t' \
              + reduce(str.__add__, ['outgoing={\n\t\tname=' + outgoing[0] \
                                     + '\n\t\tpath={\n\t\t\t' + ' '.join(outgoing[1]) \
                                     + '\n\t\t}' \
                                     + '\n\t\tcontrol={\n\t\t\t' + ' '.join(outgoing[2]) \
                                     + '\n\t\t}' \
                                     + '\n\t}\n\t' for outgoing in set(v['outgoing'])], '') \
              + 'members={\n\t\t' + ' '.join(v['members']) + '\n\t}\n' + '\tend=yes\n' * int(
            len(v['outgoing']) == 0) + '}\n'

        return out

    out = ''
    for k, v in node_data.items():
        # print(v['outgoing'])
        out += gen_node_text(k, v)
    print('nodes_text generated')
    return out

if __name__ == '__main__':
    if RELOAD_SAVE_DATA:
        node_data, countries = get_node_data()
        with open('node_data.json', 'w') as f:
            json.dump(node_data, f)
        with open('countries.json', 'w') as f:
            json.dump(countries, f)
    else:
        with open('node_data.json', 'r') as f:
            node_data = json.load(f)
        with open('countries.json', 'r') as f:
            countries = json.load(f)
        for value in node_data.values():
            value['node_connections'] = tlist(map(lambda x: (x[0], tuple(x[1]), tuple(x[2])), value['node_connections']))
    node_rank_by_country = rank_nodes_by_countries(countries, node_data)
    node_rank = dict(zip(sorted(list(node_data.keys()),
                       key=lambda x: node_score(node_data, node_rank_by_country)(x), reverse=True),
                         [i for i in range(1, len(node_data.keys())+1)]))
    print('top 10 nodes:', list(node_rank.keys())[:10])
    end_nodes = list(node_rank.keys())[:N_END_NODES]
    node_data = make_outgoing(END_NODE_RESTRICTION)(node_data, node_rank, end_nodes)
    nodes_text = gen_nodes_text(node_data)
    if not os.path.exists(os.path.join(mod_path, node_data_path)):
        os.makedirs(os.path.join(mod_path, node_data_path))
    with open(os.path.join(mod_path, node_data_path, '00_tradenodes.txt'), 'w') as f:
        f.write(nodes_text)
    shutil.copy('descriptor.mod', os.path.join(mod_path, 'descriptor.mod'))
    shutil.copy('dynamic_trade.mod', os.path.join(all_mod_folder, 'dynamic_trade.mod'))
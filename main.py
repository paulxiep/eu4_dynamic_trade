import json
import logging
import operator
import os
import shutil

import yaml

from get_node_data import get_node_data
from util import *

logging.basicConfig(level=logging.INFO)


def load_settings():
    with open('settings.yaml', 'r') as f:
        settings = yaml.safe_load(f)
    return settings


def generate_mod():
    def rank_nodes_by_countries(countries, node_data):
        all_nodes = {}
        # order = 1
        starter = {'development_cooperative': 0, 'power_cooperative': 0,
                   'development_mercantilism_cooperative': 0, 'power_mercantilism_cooperative': 0}
        for country, country_dict in countries.items():
            if country_dict['trade_port'] is not None:
                try:
                    country_node = list(filter(lambda x: country_dict['trade_port'] in x[1],
                                               [(key, value['members']) for key, value in node_data.items()]))[0][0]

                    if country_node not in all_nodes.keys():
                        all_nodes[country_node] = {'development': country_dict['development'],
                                                   'power': country_dict['power'],
                                                   'development_mercantilism': country_dict['development'] *
                                                                               country_dict['mercantilism'],
                                                   'power_mercantilism': country_dict['power'] * country_dict[
                                                       'mercantilism'],
                                                   **starter.copy()}

                    all_nodes[country_node]['development_cooperative'] += country_dict['development']
                    all_nodes[country_node]['power_cooperative'] += country_dict['power']
                    all_nodes[country_node]['development_mercantilism_cooperative'] += country_dict['development'] * \
                                                                                       country_dict['mercantilism']
                    all_nodes[country_node]['power_mercantilism_cooperative'] += country_dict['power'] * country_dict[
                        'mercantilism']
                except:
                    logging.warning(f'failed {country}, {country_dict}')
        return all_nodes

    def make_outgoing_restricted(node_data, node_rank, end_nodes):
        def min_with_index(iterator):
            min_index, min_value = min(enumerate(iterator), key=operator.itemgetter(1))
            # return (n_end_nodes - min_index) + (20 - min_value) * 1000
            return (min_value + min_index * 0.01)

        distance = 1
        nodes_at_distance = [[end_node] for end_node in end_nodes]
        for i, end_node in enumerate(end_nodes):
            node_data[end_node]['distance'] = [0 if j == i else 1 for j in range(n_end_nodes)]
            node_data[end_node]['outgoing'] = []
        all_nodes = [[end_node] for end_node in end_nodes]
        # all_nodes = [[] for _ in range(n_end_nodes)]
        while any([len(nodes_at_distance[i]) > 0 for i in range(n_end_nodes)]):
            for i in range(n_end_nodes):
                logging.info(f'{distance}, {nodes_at_distance[i]}')
                new_nodes_at_distance = []
                for node in nodes_at_distance[i]:
                    for connection in node_data[node]['node_connections']:
                        if node_data[connection[0]].get('distance', None) is None:
                            node_data[connection[0]]['distance'] = [None for _ in range(n_end_nodes)]
                        if isinstance(node_data[connection[0]]['distance'], list) and \
                                node_data[connection[0]]['distance'][
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
                             node_pull(node_data, node_rank)(connection[0], node)) \
                            and not any([node_data[connection[0]]['distance'][j] is not None \
                                         and node_data[connection[0]]['distance'][j] <
                                         node_data[connection[0]]['distance'][
                                             i] for j in range(0, i)])) \
                                and node_data[node]['node_connections'][
                            node_data[node]['node_connections'].index(connection[0])] not in node_data[node].get(
                            'outgoing',
                            []):
                            node_data[connection[0]]['outgoing'] = node_data[connection[0]].get('outgoing', []) + [
                                node_data[connection[0]]['node_connections'][
                                    node_data[connection[0]]['node_connections'].index(node)]]
                            logging.info(f'{connection[0]}->{node}')
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
        return dict(sorted(node_data.items(), key=lambda x: NodeScores(2).set_scores(
            [min_with_index([(x[1]['distance'][i]) for i in range(n_end_nodes)]), node_rank[x[0]]]), reverse=True))

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

        return dict(sorted(node_data.items(), key=lambda x: node_rank[x[0]], reverse=True))

    def node_score(node_data, node_rank, equal_threshold=1):
        def get_score(node):
            starter = {'development_cooperative': 0, 'power_cooperative': 0,
                       'development_mercantilism_cooperative': 0, 'power_mercantilism_cooperative': 0,
                       'development': 0, 'power': 0,
                       'development_mercantilism': 0, 'power_mercantilism': 0
                       }
            score = NodeScores(len(flow_power_rules), equal_threshold=equal_threshold)
            for i, flow_power_rule in enumerate(flow_power_rules):
                if flow_power_rule == 'country_development':
                    score.scores[i] = node_rank.get(node, starter)['development']
                if flow_power_rule == 'country_development_cooperative':
                    score.scores[i] = node_rank.get(node, starter)['development_cooperative']
                if flow_power_rule == 'country_development_mercantilism':
                    score.scores[i] = node_rank.get(node, starter)['development_mercantilism']
                if flow_power_rule == 'country_development_mercantilism_cooperative':
                    score.scores[i] = node_rank.get(node, starter)['development_mercantilism_cooperative']
                if flow_power_rule == 'country_power':
                    score.scores[i] = node_rank.get(node, starter)['power']
                if flow_power_rule == 'country_power_cooperative':
                    score.scores[i] = node_rank.get(node, starter)['power_cooperative']
                if flow_power_rule == 'country_power_mercantilism':
                    score.scores[i] = node_rank.get(node, starter)['power_mercantilism']
                if flow_power_rule == 'country_power_mercantilism_cooperative':
                    score.scores[i] = node_rank.get(node, starter)['power_mercantilism_cooperative']
                if flow_power_rule == 'total_development':
                    score.scores[i] = node_data[node]['development']
                if flow_power_rule == 'total_provincial_trade_power':
                    score.scores[i] = node_data[node]['trade_power']
                if flow_power_rule == 'average_provincial_trade_power':
                    score.scores[i] = node_data[node]['trade_power'] / len(node_data[node]['members'])
                if flow_power_rule == 'average_development':
                    score.scores[i] = (node_data[node]['tax'] + node_data[node]['production'] + node_data[node][
                        'manpower']) / len(node_data[node]['members'])
                if flow_power_rule == 'quadratic_total_development':
                    score.scores[i] = node_data[node]['quadratic_development']
                if flow_power_rule == 'quadratic_total_provincial_trade_power':
                    score.scores[i] = node_data[node]['quadratic_trade_power']
                if flow_power_rule == 'quadratic_average_provincial_trade_power':
                    score.scores[i] = node_data[node]['quadratic_trade_power'] / len(node_data[node]['members'])
                if flow_power_rule == 'quadratic_average_development':
                    score.scores[i] = node_data[node]['quadratic_development'] / len(node_data[node]['members'])
            # print(node, score)
            return score

        return get_score

    def node_pull(node_data, node_rank):
        def compare_nodes(first, second):
            return node_rank[first] > node_rank[second]

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
            out += gen_node_text(k, v)
        logging.info('nodes_text generated')
        return out

    def gen_mod_text(eu4_mod_folder, mod_name):
        return f'name = "dynamic_trade"\nnormal_or_historical_nations = yes\nsupported_version = "1.34.*"\npath = "{os.path.join(eu4_mod_folder, mod_name)}"'.replace('\\', '/')


    settings = load_settings()
    eu4_mod_folder = settings['file_path']['eu4_mod_folder']
    mod_name = settings['file_path']['mod_name']
    node_data_folder = settings['file_path']['node_data_folder']
    n_end_nodes = settings['flow_rules']['n_end_nodes']
    flow_power_rules = settings['flow_rules']['flow_power_rules']
    end_node_restriction = settings['flow_rules']['end_node_restriction']
    equal_threshold = settings['flow_rules']['equal_threshold']
    reload_save_data = settings['reload_save_data']
    if reload_save_data:
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
            value['node_connections'] = tlist(
                map(lambda x: (x[0], tuple(x[1]), tuple(x[2])), value['node_connections']))
    node_rank_by_country = rank_nodes_by_countries(countries, node_data)
    node_rank = dict(sorted(zip(node_data.keys(),
                                map(lambda x: node_score(node_data, node_rank_by_country, equal_threshold)(x),
                                    node_data.keys())),
                            key=lambda x: x[1], reverse=True))
    logging.info(
        f'top 10 nodes: \n' + '\n'.join(list(map(lambda x: f'{str(x[0])}: {str(x[1])}', node_rank.items()))[:10]))
    end_nodes = list(node_rank.keys())[:n_end_nodes]
    node_data = make_outgoing(end_node_restriction)(node_data, node_rank, end_nodes)
    nodes_text = gen_nodes_text(node_data)
    if not os.path.exists(os.path.join(eu4_mod_folder, node_data_folder)):
        os.makedirs(os.path.join(eu4_mod_folder, node_data_folder))
    with open(os.path.join(eu4_mod_folder, mod_name, 'common/tradenodes', '00_tradenodes.txt'), 'w') as f:
        f.write(nodes_text)
    with open(os.path.join(eu4_mod_folder, f'{mod_name}.mod'), 'w') as f:
        f.write(gen_mod_text(eu4_mod_folder, mod_name))
    shutil.copy('descriptor.mod', os.path.join(eu4_mod_folder, mod_name, 'descriptor.mod'))


if __name__ == '__main__':
    generate_mod()

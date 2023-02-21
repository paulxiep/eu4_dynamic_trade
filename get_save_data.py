import logging
import os
import re
from multiprocessing import Pool
from time import time

import yaml

with open('settings.yaml', 'r') as f:
    save_file = yaml.safe_load(f)['file_path']['save_file']


def get_province_data(save_data):
    try:
        owner = re.search('\n\t\towner="(\w+)"', save_data).group(1)
    except:
        owner = None
    try:
        tax = int(re.search('base_tax=(\d*).', save_data).group(1))
    except:
        # print('tax problem')
        tax = 1
    try:
        production = int(re.search('base_production=(\d*).', save_data).group(1))
    except:
        # print('production problem')
        production = 1
    try:
        manpower = int(re.search('base_manpower=(\d*).', save_data).group(1))
    except:
        # print('manpower problem')
        manpower = 1
    try:
        trade_power = float(re.search('trade_power=(\d*.\d*)\n', save_data).group(1))
    except:
        # print('trade power problem')
        trade_power = 0
    return {'tax': tax, 'production': production, 'manpower': manpower,
            'development': tax + production + manpower,
            'trade_power': trade_power, 'owner': owner}


def get_provinces_data(save_data):
    partial_save_list = []
    i = 1
    save_data = save_data.split(f'-{i}=' + '{', 1)
    while len(save_data) > 1:
        save_data = save_data[1].split(f'-{i + 1}=' + '{\n', 1)
        partial_save_list.append(save_data[0])
        i += 1
    with Pool(os.cpu_count() // 2) as p:
        results = p.map(get_province_data, partial_save_list)
    return {str(i + 1): results[i] for i in range(len(results))}


# def get_provinces_data_old(save_data):
#     province_data = {}
#     i = 1
#     save_data = save_data.split(f'-{i}='+'{', 1)[1]
#     while i < 4940:
#         save_data = save_data.split(f'-{i+1}='+'{\n', 1)
#         try:
#             owner = re.search('\n\t\towner="(\w+)"', save_data[0]).group(1)
#         except:
#             owner = None
#         try:
#             tax = int(re.search('base_tax=(\d*).', save_data[0]).group(1))
#         except:
#             tax = 1
#         try:
#             production = int(re.search('base_production=(\d*).', save_data[0]).group(1))
#         except:
#             production = 1
#         try:
#             manpower = int(re.search('base_manpower=(\d*).', save_data[0]).group(1))
#         except:
#             manpower = 1
#         try:
#             trade_power = float(re.search('trade_power=(\d*.\d*)\n', save_data[0]).group(1))
#             province_data[str(i)] = {'tax': tax, 'production': production, 'manpower': manpower,
#                                      'development': tax+production+manpower,
#                                      'trade_power': trade_power, 'owner': owner}
#         except:
#             pass
#         save_data = save_data[1]
#         i += 1
#     return province_data

def get_country_data(country, save_data):
    if country is None:
        return {'development': 0, 'trade_port': None, 'great_power_score': 0, 'mercantilism': 0}
    local_data = save_data.split(f'\n\t{country}', 1)[1]
    return {'development': int(re.search('\t\traw_development=(\d*).', local_data).group(1)),
            'trade_port': re.search('\t\ttrade_port=(\d*)\n', local_data).group(1),
            'power': float(re.search('\t\tgreat_power_score=(\d*.\d*)\n', local_data).group(1)),
            'mercantilism': float(re.search('\t\tmercantilism=(\d*.\d*)\n', local_data).group(1))}
    # return (int(re.search('\t\traw_development=(\d*).', local_data).group(1)),
    #         re.search('\t\ttrade_port=(\d*)\n', local_data).group(1))


def get_save_data():
    with open(save_file, 'r') as f:
        save_data = f.read()
    logging.info('save data read')
    last_time = time()
    province_data = get_provinces_data(save_data)
    logging.info(f'province data extracted, took {time() - last_time} seconds')
    last_time = time()
    countries = set([province['owner'] for province in province_data.values()])
    countries = {country: get_country_data(country, save_data) for country in countries}
    # print(list(countries.items()))
    logging.info(f'country data extracted, took {time() - last_time} seconds')
    # countries = dict(sorted(countries.items(), key=lambda x: x[1]['development'], reverse=True))
    return province_data, countries

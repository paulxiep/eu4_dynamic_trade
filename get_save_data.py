import json
import operator
from functools import reduce
import os
import yaml
import re
from util import *

with open('settings.yaml', 'r') as f:
    save_file = yaml.safe_load(f)['file_path']['save_file']
# save_file = '/Users/paulx/Documents/Paradox Interactive/Europa Universalis IV/save games/Xie Kamchatka 4.eu4'

def get_province_data(save_data):
    province_data = {}
    i = 1
    save_data = save_data.split(f'-{i}='+'{', 1)[1]
    while i < 4940:
        save_data = save_data.split(f'-{i+1}='+'{\n')
        try:
            owner = re.search('\n\t\towner="(\w+)"', save_data[0]).group(1)
        except:
            owner = None
        try:
            tax = int(re.search('base_tax=(\d*).', save_data[0]).group(1))
        except:
            tax = 1
        try:
            production = int(re.search('base_production=(\d*).', save_data[0]).group(1))
        except:
            production = 1
        try:
            manpower = int(re.search('base_manpower=(\d*).', save_data[0]).group(1))
        except:
            manpower = 1
        try:
            trade_power = float(re.search('trade_power=(\d*.\d*)\n', save_data[0]).group(1))
            province_data[str(i)] = {'tax': tax, 'production': production, 'manpower': manpower,
                                     'trade_power': trade_power, 'owner': owner}
        except:
            pass
        save_data = save_data[1]
        i += 1
    return province_data

def get_country_data(country, save_data):
    if country is None:
        return 0, None
    local_data = save_data.split(f'\n\t{country}', 1)[1]
    return (int(re.search('\t\traw_development=(\d*).', local_data).group(1)),
            re.search('\t\ttrade_port=(\d*)\n', local_data).group(1))

def get_save_data():
    with open(save_file, 'r') as f:
        save_data = f.read()
    print('save data read')
    province_data = get_province_data(save_data)
    print('province data extracted')
    countries = set([province['owner'] for province in province_data.values()])
    countries = {country: get_country_data(country, save_data) for country in countries}
    print('country data extracted')
    countries = dict(sorted(countries.items(), key=lambda x: x[1][0], reverse=True))
    return province_data, countries
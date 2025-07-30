# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Kevin De Bruycker and Stijn D'hollander
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import numpy as np
import pandas as pd
import csv
import re
from collections import defaultdict
import datetime
from InitDecaytor import time_factors

supported_sources = {
    'SpyControl v3': 'spycontrolv3',
    'SpyControl v1': 'spycontrolv1',
}
source_encoding = {
    'spycontrolv3': 'utf-8',
    'spycontrolv1': 'ansi',
}

def import_spycontrolv3_data(csvfile: str = None, StringIO = None):
    if csvfile is not None:
        with open(csvfile, newline='', encoding='utf-8') as file:
            data = csv.reader(file, delimiter=';')
            data_dict = defaultdict(list)
            for row in data:
                if row:
                    name = re.fullmatch(r'\[(\w*)\]', row[0])
                    data_dict[name[1].lower()].append(row[1:]) if name else data_dict['datapoints'].append(row[1:])
    elif StringIO is not None:
        data = csv.reader(StringIO, delimiter=';')
        data_dict = defaultdict(list)
        for row in data:
            if row:
                name = re.fullmatch(r'\[(\w*)\]', row[0])
                data_dict[name[1].lower()].append(row[1:]) if name else data_dict['datapoints'].append(row[1:])
    else:
        return None

    df = pd.DataFrame(data_dict['datapoints'], columns=data_dict['data'], dtype=float)
    df = df.mul(np.float_power(np.full(len(data_dict['exponent'][0]), 10), np.array(data_dict['exponent'][0], dtype=int)))

    starttime = datetime.datetime.combine(datetime.datetime.strptime(data_dict['date'][0][0], "%d.%m.%Y").date(),
                                          datetime.time.fromisoformat(data_dict['time'][0][0] + "00"))

    retain_columns = {'time': 'time', 'TIntern': 'T_intern', 'TProcess': 'T_process', 'Setpoint': 'T_set'}
    df = df[[x for x in retain_columns]]
    df.columns = [retain_columns[x] for x in retain_columns]
    units = {data: unit.replace('-', '') for data, unit in zip(data_dict['data'][0], data_dict['unit'][0])}
    units = {retain_columns[x]: units[x] for x in units if x in retain_columns}

    return {
        'starttime': starttime,
        'data': df,
        'units': units,
        'timeunit': units['time']
    }

def import_spycontrolv1_data(csvfile: str = None, StringIO = None):
    if csvfile is not None:
        with open(csvfile, newline='', encoding='ansi') as file:
            data = csv.reader(file, delimiter=';')
            datapoints = []
            data_flag = False
            i = 0
            for row in data:
                if row:
                    if not i and row[0] == '§':
                        starttime = datetime.datetime.combine(
                            datetime.datetime.strptime(row[1], "%d.%m.%Y").date(),
                            datetime.time.fromisoformat(row[2]))
                    else:
                        name = re.fullmatch(r'\[(\w*)\]', row[0])
                        if name:
                            data_flag = True if name[1].lower() == 'data' else False
                        elif data_flag:
                            if not i:
                                header = row
                            else:
                                datapoints.append(row)
                            i += 1
    elif StringIO is not None:
        data = csv.reader(StringIO, delimiter=';')
        datapoints = []
        data_flag = False
        i = 0
        for row in data:
            if row:
                if not i and row[0] == '§':
                    starttime = datetime.datetime.combine(
                        datetime.datetime.strptime(row[1], "%d.%m.%Y").date(),
                        datetime.time.fromisoformat(row[2]))
                else:
                    name = re.fullmatch(r'\[(\w*)\]', row[0])
                    if name:
                        data_flag = True if name[1].lower() == 'data' else False
                    elif data_flag:
                        if not i:
                            header = row
                        else:
                            datapoints.append(row)
                        i += 1
    else:
        return None

    columns = []
    units = {}
    for entry in header:
        column = re.sub(r'\s*\[(.*)\]', '', entry)
        unit = re.search(r'\[(.*)\]', entry)
        columns.append(column)
        units[column] = unit.groups()[0] if unit else ""

    df = pd.DataFrame(datapoints, columns=columns)  # , dtype=float

    retain_columns = {'Date|Time': 'time', 'Tjacket': 'T_intern', 'Tprocess': 'T_process', 'Setpoint': 'T_set'}
    df = df[[x for x in retain_columns]]
    df.columns = [retain_columns[x] for x in retain_columns]
    for column in df.columns:
        try:
            df[column] = df[column].astype(float)
        except:
            df[column] = df[column].str.replace(',', '.').astype(float)
    df['time'] -= df['time'].min()
    df['time'] *= 86400     # 24h in seconds
    units = {retain_columns[x]: units[x] for x in units if x in retain_columns}
    units['time'] = 's'

    return {
        'starttime': starttime,
        'data': df,
        'units': units,
        'timeunit': units['time']
    }


def get_temperature_profile(csvfile: str = None,
                            StringIO = None,
                            source = 'spycontrolv3',
                            ):
    if source == 'spycontrolv3':
        tmp = import_spycontrolv3_data(csvfile, StringIO)
        time_factor = time_factors[tmp['units']['time']]
        tmp['data']['time'] *= time_factor
        return tmp['data'][['time', 'T_process']].values.tolist()
    elif source == 'spycontrolv1':
        tmp = import_spycontrolv1_data(csvfile, StringIO)
        time_factor = time_factors[tmp['units']['time']]
        tmp['data']['time'] *= time_factor
        return tmp['data'][['time', 'T_process']].values.tolist()
    return None



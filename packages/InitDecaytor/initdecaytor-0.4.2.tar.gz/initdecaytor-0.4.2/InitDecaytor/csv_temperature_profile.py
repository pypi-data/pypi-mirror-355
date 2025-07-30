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


def import_spycontrol_data(csvfile: str = None, StringIO = None):
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

def get_temperature_profile(csvfile: str = None,
                            StringIO = None,
                            source = 'spycontrol',
                            ):
    if source == 'spycontrol':
        tmp = import_spycontrol_data(csvfile, StringIO)
        time_factor = time_factors[tmp['units']['time']]
        tmp['data']['time'] *= time_factor
        return tmp['data'][['time', 'T_process']].values.tolist()
    return None



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
from scipy.optimize import fsolve
# from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from numba import njit

# function to calculate hlt in seconds t1/2 = 60 * np.float_power(10, A / T + B) with A and B:
hlt_parms = {
    # 'ini': [A, B]
    "Vazo52": [6767, -18.037],
    "Vazo64": [7142, -18.355],
    "Vazo67": [7492, -19.215],
    "Vazo88": [7660, -18.39],
    "V601": [6634, -16.783], # calculated based on 10h-hlT of 66°C and Ea = 1.27E5 J/mol
    "BPO": [7313, -18.048], # calculated based on 10h-hlT of 78°C and Ea = 140E3 J/mol (https://www.sciencedirect.com/topics/chemistry/benzoyl-peroxide, https://doi.org/10.1016/B978-008043417-9/50046-5)
    "Luperox 101": [8122, -18.147], # calculated based on 10h-hlT of 115°C and Ea = 155.49E3 J/mol (Brochure Nouryon, = Trigonox 101)
    "Luperox 130": [7870, -17.241], # calculated based on 10h-hlT of 120°C and Ea = 150.67E3 J/mol (Brochure Nouryon, = Trigonox 145)
    "Vazo56WSx": [6426, -16.75],
    "Vazo68WSP": [5920, -14.58],
}

def decay_function(time, c0, T, A, B, target_c = 0.):
    return c0 * np.exp(-time * np.log(2) / (60 * np.float_power(10, A / T + B))) - target_c

@njit
def calculate_decay(time_step, c0, T, A, B):
    c = np.empty_like(c0)
    c[0] = c0[0]
    for i in range(1, len(c0)):
        c[i] = c[i - 1] * np.exp(-time_step[i] * np.log(2) / (60 * np.float_power(10, A / T[i] + B))) + c0[i]
    return c

time_factors = {
    "s": 1,
    "min": 60,
    "h": 3600,
}


'''
def initiator_concentration(time, initiator_charge, temperature, initiator):
    if type(initiator_charge) == float or type(initiator_charge) == int:
        c0 = np.zeros(len(time))
        c0[0] = initiator_charge
    else:
        assert len(initiator_charge) == len(time), "Length of initiator_charge does not equal that of time. Check input."
        c0 = np.array(initiator_charge)
    if type(temperature) == float or type(temperature) == int:
        T = np.full(len(time), temperature)
    else:
        assert len(temperature) == len(time), "Length of temperature does not equal that of time. Check input."
        # shift T one right to calculate the conversion on T at c0
        T = np.concatenate([[temperature[0]], temperature[:-1]])
    time_step = np.diff(time, prepend=0.0)
    return calculate_decay(c0, time_step, T, hlt_parms[initiator][0], hlt_parms[initiator][1])
'''
'''
def determine_end_time(time, rel_concentration, temperature, initiator, threshold):
    time_step = fsolve(decay_function, x0=1.0, args=(rel_concentration, temperature, hlt_parms[initiator][0], hlt_parms[initiator][1], threshold))
    return time + int(time_step[0]) + 1
'''
'''
def add_data_to_df(df, reference_column: str, target_column: str, referenced_data: list or tuple, fill_value):
    if target_column in df.columns:
        ref_in_df = np.array(df[target_column])
    else:
        ref_in_df = np.full(len(df), fill_value, dtype='float64')
    ref_not_in_df = []
    for ref, data in referenced_data:
        if not df[df[reference_column] == ref].empty:
            ref_in_df[df[df[reference_column] == ref].index] = data
        else:
            ref_not_in_df.append([ref, data])
    df[target_column] = ref_in_df
    if ref_not_in_df:
        df = pd.concat([df, pd.DataFrame(ref_not_in_df, columns=[reference_column, target_column])], ignore_index=True)
        df.sort_values(reference_column, inplace=True, ignore_index=True)
    return df
'''
'''
def fix_df(df):
    if len(df) < df.iloc[-1]['time'] + 1:
        temp = pd.DataFrame({'time': np.arange(df.iloc[-1]['time'] + 1, dtype='float64'),})
        df = temp.merge(df, on='time', how='left')
    # Fill generated gaps in temperature
    df.loc[df.temperature.isna(), 'temperature'] = np.interp(df.time[df.temperature.isna()],
                                                             df.time[~df.temperature.isna()],
                                                             df.temperature[~df.temperature.isna()])
    df.fillna(0, inplace=True)
    return df
'''



class Simulation:
    def add_data(self, reference_column: str, target_column: str, referenced_data: list or tuple, fill_value):
        if target_column in self.data.columns:
            ref_in_df = np.array(self.data[target_column])
        else:
            ref_in_df = np.full(len(self.data), fill_value, dtype='float64')
        ref_not_in_df = []
        for ref, data in referenced_data:
            if not self.data[self.data[reference_column] == ref].empty:
                ref_in_df[self.data[self.data[reference_column] == ref].index] = data
            else:
                ref_not_in_df.append([ref, data])
        self.data[target_column] = ref_in_df
        if ref_not_in_df:
            self.data = pd.concat([self.data, pd.DataFrame(ref_not_in_df, columns=[reference_column, target_column])],
                                  ignore_index=True)
            self.data.sort_values(reference_column, inplace=True, ignore_index=True)

    def fix_data(self):
        # if len(self.data) < self.data.iloc[-1]['time'] + 1:
        temp = pd.DataFrame({'time': np.arange(self.data.iloc[-1]['time'] + 1, dtype='float64')})
        self.data = temp.merge(self.data, on='time', how='outer')
        # Fill generated gaps in temperature
        self.data.loc[self.data.temperature.isna(), 'temperature'] = np.interp(self.data.time[self.data.temperature.isna()],
                                                                               self.data.time[~self.data.temperature.isna()],
                                                                               self.data.temperature[~self.data.temperature.isna()])
        # Fill gaps in initiator charges, errors in concentrations will be fixed when recalculating
        self.data.fillna(0, inplace=True)

    '''
    def determine_end_time(self, initiator):
        tmp = fsolve(decay_function, x0=1.0,
                           args=(self.data.iloc[-1][initiator + '_rel_concentration'], self.data.iloc[-1]['temperature'], hlt_parms[initiator][0], hlt_parms[initiator][1],
                                 self.trim_threshold))
        return self.data.iloc[-1]['time'] + int(tmp[0]) + 1
    '''

    def calculate_concentrations(self):
        # Calculate concentrations
        recalculate = True
        while recalculate:
            recalculate = False
            for initiator in hlt_parms:
                if initiator + '_charges' in self.data.columns:
                    time_step = np.diff(self.data['time'], prepend=0.0)
                    c0 = self.data[initiator + '_charges'].to_numpy()
                    # shift T one right to calculate the conversion on T at c0
                    T = np.concatenate([[self.data['temperature'][0]], self.data['temperature'][:-1]])
                    self.data[initiator + "_concentration"] = calculate_decay(time_step, c0, T, hlt_parms[initiator][0], hlt_parms[initiator][1])
                    self.data[initiator + "_rel_concentration"] = self.data[initiator + "_concentration"] / self.data[initiator + "_concentration"].max()
                    # Extend end-time of simulation if required
                    if not self.time_limit and self.data.iloc[-1][initiator + '_rel_concentration'] > self.trim_threshold:
                        # Determine end time and fix dataframe
                        end_time = fsolve(decay_function, x0=1.0,
                                          args=(self.data.iloc[-1][initiator + '_rel_concentration'],
                                                self.data.iloc[-1]['temperature'], hlt_parms[initiator][0],
                                                hlt_parms[initiator][1],
                                                self.trim_threshold))
                        end_time = self.data.iloc[-1]['time'] + int(end_time[0]) + 1
                        self.data = pd.concat([self.data, pd.DataFrame({'time': [end_time]})], ignore_index=True)
                        self.fix_data()
                        recalculate = True
        # Trim df
        if self.trim_data:
            self.data.drop(self.data[self.data['time'] > self.data['time'][(self.data[self.data.columns[
                self.data.columns.to_series().str.contains('_rel_concentration')]] >= self.trim_threshold).any(
                axis=1)].max()].index, inplace=True)
        if self.time_limit:
            self.data.drop(self.data[self.data['time'] > self.time_limit * self.time_factor].index, inplace=True)

    def __init__(self,
                 temperature: float or int,
                 time_limit: float = 0,
                 time_unit: str = 'h',
                 initiator_charges: list = None,
                 initiator_charges_unit: str = 'wt%',
                 trim_data: bool = True,
                 trim_threshold: float = 1e-4,
                 ):

        self.temperature = temperature
        self.time_limit = time_limit
        self.time_unit = time_unit
        self.initiator_charges = initiator_charges
        self.initiator_charges_unit = initiator_charges_unit
        self.trim_data = trim_data
        self.trim_threshold = trim_threshold

        self.time_factor = time_factors[time_unit]

        if not time_limit:
            time = np.arange(1 + self.time_factor, dtype='float64')
        else:
            time = np.arange(1 + time_limit * self.time_factor, dtype='float64')

        # Initialize dataframe
        self.data = pd.DataFrame({
            'time': time,
        })

        # Add temperature
        if type(temperature) == float or type(temperature) == int:
            self.data['temperature'] = np.full(len(time), temperature + 273.15)
        else:
            self.add_data('time', 'temperature', temperature, np.nan)
            self.data['temperature'] += 273.15

        # Put initiator charges in dataframe
        if initiator_charges:
            for initiator, time, charge in initiator_charges:
                assert initiator in hlt_parms, "No kinetic data available for {0} available. Check initiator_loadings.".format(initiator)
                self.add_data('time', initiator + '_charges', [[time * self.time_factor, charge]], 0)
            # Fix dataframe
            self.fix_data()
            # Calculate the concentration as a function of time
            self.calculate_concentrations()

    def set_initiator_charges(self,
                              initiator_charges: list,
                              ):
        self.initiator_charges = initiator_charges
        # Delete old charges
        for initiator in hlt_parms:
            if initiator + '_charges' in self.data.columns:
                self.data.drop(initiator + '_charges', axis=1, inplace=True)
            if initiator + '_concentration' in self.data.columns:
                self.data.drop(initiator + '_concentration', axis=1, inplace=True)
                self.data.drop(initiator + '_rel_concentration', axis=1, inplace=True)
        for initiator, time, charge in initiator_charges:
            assert initiator in hlt_parms, "No kinetic data available for {0} available. Check initiator_loadings.".format(initiator)
            self.add_data('time', initiator + '_charges', [[time * self.time_factor, charge]], 0)
        # Fix dataframe
        self.fix_data()
        # Calculate the concentration as a function of time
        self.calculate_concentrations()

    def set_time_unit(self,
                      time_unit: str,
                      ):
        assert time_unit in time_factors, "Invalid time unit. Check input."
        if self.initiator_charges:
            initiator_charges = [[initiator, time * self.time_factor, charge] for initiator, time, charge in self.initiator_charges]
        self.time_unit = time_unit
        self.time_factor = time_factors[time_unit]
        if self.initiator_charges:
            initiator_charges = [[initiator, time / self.time_factor, charge] for initiator, time, charge in initiator_charges]
            self.set_initiator_charges(initiator_charges)

    def plot_data(self,
                  plot_relative_concentration: bool = True,
                  engine = 'plotly',
                  ):
        data_reduced = self.data.iloc[::int(len(self.data) / 65536) + 1]
        if engine == 'plotly':
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            for ini in hlt_parms:
                if ini + '_concentration' in data_reduced.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=data_reduced['time'] / self.time_factor,
                            y=data_reduced[ini + '_rel_concentration'] * 100,
                            mode='lines',
                            name=ini,
                            hovertemplate=f'%{{y:.4f}}% after %{{x:.2f}}{self.time_unit}',
                        ) if plot_relative_concentration else (
                            go.Scatter(
                                x=data_reduced['time'] / self.time_factor,
                                y=data_reduced[ini + '_concentration'],
                                mode='lines',
                                name=ini,
                                hovertemplate=f'%{{y:.4f}}{self.initiator_charges_unit} after %{{x:.2f}}{self.time_unit}',
                            )),
                        secondary_y=False,
                    )
            fig.add_trace(
                go.Scatter(
                    x=data_reduced['time'] / self.time_factor,
                    y=data_reduced['temperature'] - 273.15,
                    mode='lines',
                    line={'dash': 'dot', 'color': 'gray'},
                    name="Temperature",
                    showlegend=False,
                ),
                secondary_y=True,
            )
            fig.update_xaxes(title_text='Time ({})'.format(self.time_unit))
            fig.update_yaxes(
                title_text='Rel. concentration (%)' if plot_relative_concentration else 'Concentration ({0})'.format(
                    self.initiator_charges_unit), secondary_y=False)
            fig.update_yaxes(title_text='Temperature (°C)', secondary_y=True)
            return fig
        elif engine == 'matplotlib':
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()
            ax1.set_zorder(ax2.get_zorder() + 1)
            ax1.patch.set_visible(False)
            for ini in hlt_parms:
                if ini + '_concentration' in data_reduced.columns:
                    ax1.plot(data_reduced['time'].to_numpy() / self.time_factor,
                             data_reduced[ini + '_rel_concentration'].to_numpy() * 100,
                             label=ini) if plot_relative_concentration else ax1.plot(
                        data_reduced['time'].to_numpy() / self.time_factor, data_reduced[ini + '_concentration'].to_numpy(),
                        label=ini)
            ax2.plot(data_reduced['time'].to_numpy() / self.time_factor, data_reduced['temperature'].to_numpy() - 273.15, ':')
            ax1.set_xlabel('Time ({})'.format(self.time_unit))
            ax1.set_ylabel('Rel. concentration (%)') if plot_relative_concentration else ax1.set_ylabel(
                'Concentration ({0})'.format(self.initiator_charges_unit))
            ax2.set_ylabel('Temperature (°C)')
            legend = ax1.legend()
            # legend.set_zorder(20)
            return plt
        return None

    def show_plot(self,
                  plot_relative_concentration: bool = True,
                  engine='plotly',
                  plotly_renderer=None,
                  ):
        fig = self.plot_data(plot_relative_concentration, engine)
        if engine == 'plotly' and plotly_renderer:
            fig.show(renderer=plotly_renderer)
        else:
            fig.show()

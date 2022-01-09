import re as _re
from copy import deepcopy as _copy
import webbrowser as _wb
import typing as _ty
from datetime import datetime as _dt
from datetime import date as _date
import pandas as _pd
import numpy as _np
import plotly.express as _px
import dash as _dash
from dash import dcc as _dcc
from dash import html as _html

def _df_check(dfs: dict):
    required_dfs = {'AdmissionsDiagnosesCorePopulatedTable',
                    'AdmissionsCorePopulatedTable',
                    'LabsCorePopulatedTable',
                    'PatientCorePopulatedTable'}
    if dfs.keys() != required_dfs:
        raise Exception('Dataframes are incorrectly formatted, missing dictionaried dataframes:' \
                        + str(required_dfs - dfs.keys()) \
                        + '\nPlease use load_data from the data module to load in custom data')

def summary() -> None:
    print('Hello there')
    
class IndSummary:
    
    def __init__(self, dfs: dict) -> None:
        _df_check(dfs)
        self.dfs = dfs
        
    def __call__(self, patient_id: str, browser: bool=False, port: int=8050) -> _ty.Tuple[_pd.DataFrame, _px.scatter]:
        table = self.get_core_info(patient_id)
        plots = self.get_lab_info(patient_id)
        if browser:
            self.browser(plots, port)
        return table, plots
    
    def _age_calc(self, start_date, end_date):
        year_diff = end_date.year - start_date.year
        month_diff = (end_date.month, end_date.day) < (start_date.month, start_date.day)
        return  year_diff - month_diff
    
    def get_core_info(self, patient_id: str, age_at: _dt = _dt.today().date()):
         # Get and format the core individual information
        core_info = self.dfs['PatientCorePopulatedTable'][self.dfs['PatientCorePopulatedTable'].iloc[:,0] == patient_id]    
        
        cols = core_info.columns
        col_dict = {x:_re.sub(r'Patient|(\w)([A-Z])', r'\1 \2', x).strip() for x in cols}
        col_dict['PatientID'] = 'ID'
        core_info = core_info.rename(columns=col_dict)
    
        #core_info = core_info[core_info["ID"] == patient_id]
        core_info = core_info.melt()
        core_info.columns = ['Patient_Info','values']
    
        # Format the patients birthday so it is separated between day and time
        patient_birth = _dt.strptime(
            core_info['values'].loc[core_info['Patient_Info'].str.lower() == "date of birth"].values[0],'%Y-%m-%d %H:%M:%S.%f')
        patient_bday = patient_birth.date()
        patient_btime = patient_birth.time()
    
        # Get age of person at time of request
        core_info = core_info.append(
            _pd.DataFrame([['Birthday', patient_bday.strftime('%d/%m/%Y')],
                           ['Time of Birth', patient_btime],
                           ['Age (as of '+str(age_at.strftime('%d/%m/%Y'))+')', self._age_calc(patient_birth, age_at)]],
                          columns=core_info.columns),
            ignore_index=True)
        return core_info
    
    def get_lab_info(self, patient_id: str):
        lab_info = self.dfs['LabsCorePopulatedTable'][self.dfs['LabsCorePopulatedTable'].iloc[:,0] == patient_id] 
        lab_info = lab_info.assign(LabDateTime=_pd.to_datetime(lab_info['LabDateTime']).dt.date)
        lab_info = lab_info.sort_values(by='LabDateTime')
        start_days = (lab_info[['AdmissionID','LabName','LabDateTime']]
                      .groupby(['AdmissionID', 'LabName'])
                      .min()
                      .reset_index()
                      .rename(columns={'LabDateTime':'StartDate'})
                     )
        lab_info = lab_info.merge(start_days, how = 'left', on=['AdmissionID','LabName'])
        lab_info['DayInHospital'] = (lab_info['LabDateTime'] - lab_info['StartDate']).dt.days

        lab_figs = {}
        for super_set in {x.split(':')[0] for x in lab_info['LabName']}:
            lab_fig_data = lab_info[lab_info['LabName'].str.contains(super_set)]
            if not lab_fig_data.empty:
                fig = _px.line(
                    lab_fig_data,
                    x='DayInHospital',
                    y='LabValue',
                    color='AdmissionID',
                    hover_name='LabName',
                    hover_data=['LabDateTime', 'LabUnits'],
                    facet_col='LabName',
                    facet_col_wrap=5,
                    markers=True
                )
                (fig.update_yaxes(matches=None)
                 .for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                 .for_each_annotation(lambda a: a.update(text=a.text.split(":")[-1].lower()))
                 .update_layout(hovermode='x unified', font=dict(size=8))
                 .update_traces(marker=dict(size=3))
                )
            else: fig = None
            lab_figs[super_set.lower()] = fig
        return lab_figs
    
    def browser(self, figs: dict, port: int):
        app = _dash.Dash()
        html_out = [
                _html.H1(children='Hello Dash'),
                _html.Div(children='A web app framework')
            ]
        for plot in figs.keys():
            html_out.append(_html.H2(children=plot))
            html_out.append(_dcc.Graph(id=plot, figure=figs[plot]))
            
        app.layout = _html.Div(children=html_out)
        
        _wb.open_new('http://127.0.0.1:'+str(port)+'/')
        app.run_server(port=port)
        return None

class QuickSearch:
    def __init__(self, dfs: dict):
        self.dfs = dfs
    
    def __call__(self, port: int = 8050):
        app = _dash.Dash()

        inputs = _html.Div(children=[
            _html.H2('Patient Search - Filters'),
            _html.Label('Maximum Rows to Show'),
            _dcc.Slider(min=1, max=20, value=10, marks={i: f'Row {i}' for i in range(1,21)}, id='max_rows'),
            _html.H3('Patient Info'),
            _html.Label('Patient Sex'),
            _dcc.Dropdown(options=[{'label':'Male', 'value': 'Male'},
                                  {'label':'Female', 'value':'Female'}],
                         id='sex'),
            _html.Label('Year Born'),
            _dcc.Slider(min=1900, max=_dt.now().year, value=1900, marks={i:str(i) if i != 1900 else 'Unknown' for i in range(1900, _dt.now().year+1, 10)},
                                                  id='year_born')
        ])
        outputs = _html.Div(children=[
            _html.H1('Dataframes Found'),
            _html.Div(id='tables')
        ])
        
        app.layout = _html.Div(children=[inputs, outputs])
        callback_components = app.callback(_dash.dependencies.Output('tables', 'children'),
                                           _dash.dependencies.Input('max_rows', 'value'),
                                           _dash.dependencies.Input('sex', 'value'),
                                          _dash.dependencies.Input('year_born', 'value'))
        callback_components(self.tables_out)
        
        app.run_server(port=port)
    
    def tables_out(self, max_rows, sex, birthday):
        filtered_dfs = _copy(self.dfs)
        
        self.filter_str(filtered_dfs, 'PatientCorePopulatedTable', 'PatientGender', sex, exact=True)
        
        if birthday != 1900:
            filtered_dfs['PatientCorePopulatedTable'].assign(PatientDateOfBirth=_pd.to_datetime(filtered_dfs['PatientCorePopulatedTable']['PatientDateOfBirth']).dt.date)
            filtered_dfs['PatientCorePopulatedTable'] = filtered_dfs['PatientCorePopulatedTable'][_pd.DatetimeIndex(filtered_dfs['PatientCorePopulatedTable']['PatientDateOfBirth']).year == birthday]
        self.update_remaining_tables(filtered_dfs, 'PatientCorePopulatedTable')
        
        
        children_out = [_html.Div([_html.H3(key),
                                   self.html_table(filtered_dfs[key], max_rows)]) for key in filtered_dfs.keys()]
        return children_out
    
    def update_remaining_tables(self, dfs, df_key):
        filtered_patients = dfs[df_key]['PatientID'].unique()
        for key in dfs.keys():
            if key != df_key:
                dfs[key] = dfs[key][dfs[key]['PatientID'].isin(filtered_patients)]
    
    def html_table(self, df, max_rows):
        return _html.Table([
            _html.Thead(_html.Tr([_html.Th(col) for col in df.columns])),
            _html.Tbody([_html.Tr(
                [_html.Td(df.iloc[i][col]) for col in df.columns]
            ) for i in range(min(len(df), max_rows))
            ])
        ])
    
    def filter_num(self, dfs: _pd.DataFrame, key: str, column: str, value: int, minmax: str='min'):
        if minmax == 'min':
            pass
        elif minmax == 'max':
            pass
        elif minmax == 'exact':
            pass
    
    def filter_str(self, dfs: _pd.DataFrame, key: str, column: str, text: str, exact: bool=True):
        if text is not None and text != 'Unknown':
            if exact:
                dfs[key] = dfs[key][dfs[key][column] == text]
            else:
                pass
    
    def filter_date(self, df, column, dt):
        pass
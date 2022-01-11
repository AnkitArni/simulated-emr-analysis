import re as _re
import webbrowser as _wb
from copy import deepcopy as _copy
from datetime import datetime as _dt
import logging as _logging

import dash as _dash
import pandas as _pd
import plotly.express as _px
from dash import dcc as _dcc
from dash import html as _html
from dash.dependencies import Output as _Output
from dash.dependencies import Input as _Input

# Correct logs for use with dash
_log = _logging.getLogger('werkzeug')
_log.setLevel(_logging.ERROR)


def _df_check(dfs: dict):
    """
    Checks required dataframes are in the dictionary input from 'Loader'
    Dictionary requires 'diagnosis', 'admissions', 'labs' and 'patients' keys

    Args:
        dfs (dict):
            Dictionary of EMR data, correctly formatter by data.Loader()

    Raises:
        Exception:
            Data is incorrect, gives warning message to user
    """

    required_dfs = {'diagnosis',
                    'admissions',
                    'labs',
                    'patients'}
    if dfs.keys() != required_dfs:
        raise Exception('Dataframes are incorrectly formatted, ' +
                        'missing dictionaried dataframes:' +
                        f'{required_dfs - dfs.keys()}' +
                        '\nPlease use data.Loader() to load in custom data')


class IndSummary:
    """
    Generates summary data for a requested individual
    """

    def __init__(self, dfs: dict) -> None:
        """ Initializes the class

        Args:
            dfs (dict):
                Dictionary of EMR data, correctly formatter by data.Loader()
        """

        _df_check(dfs)
        self.dfs = dfs

    def __call__(self,
                 patient_id: str,
                 browser: bool = False,
                 port: int = 8050) -> dict:
        """
        Gets the specific information about a requested person
        and returns it in a dictionary or browser window

        Args:
            patient_id (str):
                The id of the patient whose summary data is requested
            browser (bool, optional):
                If true, will open a brwser window of a Dash interactive window
                on the requested port (default 8050).
                Defaults to False.
            port (int, optional):
                The port number to start the dash server in. Defaults to 8050.

        Returns:
            dict:
                Dictionary of a pandas dataframe of basic patient information
                and dictionary of plotly plots of their recent lab statistics
        """

        info = self.get_core_info(patient_id)
        plots = self.get_lab_info(patient_id)
        if browser:
            self.browser(info, plots, port)
        return {'info': info, 'plots': plots}

    def _age_calc(self, start_date: _dt, end_date: _dt) -> int:
        """ Calculate the age of a person, given two dates
            (assumes person is not dead)

        Args:
            start_date (datetime):
                Date person is born
            end_date (datetime):
                Current date

        Returns:
            int:
                The age in years of the person
        """

        yr_diff = end_date.year - start_date.year
        mth_diff = (end_date.month, end_date.day) \
            < (start_date.month, start_date.day)
        return yr_diff - mth_diff

    def get_core_info(self, patient_id: str, age_at: _dt = _dt.today().date()):
        """ Get the patients known characteristics and information

        Args:
            patient_id (str):
                The id of the patient whose summary data is requested
            age_at (datetime, optional):
                Time at which to calculate people's age.
                Defaults to current date: datetime.today().date().
        """

        # Get and format the core individual information
        core_info = (
            self.dfs['patients'][self.dfs['patients']
                                 .iloc[:, 0] == patient_id]
        )

        cols = core_info.columns
        col_dict = {x: _re.sub(
            r'Patient|(\w)([A-Z])', r'\1 \2', x).strip() for x in cols}
        col_dict['PatientID'] = 'ID'
        core_info = core_info.rename(columns=col_dict)

        core_info = core_info.melt()
        core_info.columns = ['Patient_Info', 'Values']

        # Format the patients birthday so it is separated between day and time
        patient_birth = _dt.strptime(
            core_info['Values']
            .loc[core_info['Patient_Info'].str.lower() == 'date of birth']
            .values[0], '%Y-%m-%d %H:%M:%S.%f')
        patient_bday = patient_birth.date()
        patient_btime = patient_birth.time()
        core_info = (
            core_info
            .drop(index=core_info[
                core_info['Patient_Info'].str.lower() == 'date of birth'
            ].index))

        # Get age of person at time of request
        core_info = core_info.append(
            _pd.DataFrame([
                ['Birthday', patient_bday.strftime('%d/%m/%Y')],
                ['Time of Birth', patient_btime],
                [f'Age (as of {age_at.strftime("%d/%m/%Y")})',
                 self._age_calc(patient_birth, age_at)]],
                columns=core_info.columns),
            ignore_index=True
        )
        return core_info

    def get_lab_info(self, patient_id: str):
        """ Get's the patients lab data and plots it

        Args:
            patient_id (str):
                The id of the patient whose summary data is requested

        Returns:
            dict:
                Dictionary of plots with keys as the super type (eg, CBC etc.)
        """

        lab_info = self.dfs['labs'][self.dfs['labs'].iloc[:, 0] == patient_id]
        lab_info = lab_info.assign(LabDateTime=_pd.to_datetime(
            lab_info['LabDateTime']
        ).dt.date)
        lab_info = lab_info.sort_values(by='LabDateTime')
        start_days = (lab_info[['AdmissionID', 'LabName', 'LabDateTime']]
                      .groupby(['AdmissionID', 'LabName'])
                      .min()
                      .reset_index()
                      .rename(columns={'LabDateTime': 'StartDate'})
                      )
        lab_info = lab_info.merge(start_days,
                                  how='left',
                                  on=['AdmissionID', 'LabName'])
        lab_info['DayInHospital'] = (lab_info['LabDateTime'] -
                                     lab_info['StartDate']).dt.days

        lab_figs = {}
        for super_set in {x.split(':')[0] for x in lab_info['LabName']}:
            lab_fig_df = lab_info[lab_info['LabName'].str.contains(super_set)]
            if not lab_fig_df.empty:
                fig = _px.line(
                    lab_fig_df,
                    title=super_set + ' Data',
                    x='DayInHospital',
                    y='LabValue',
                    color='AdmissionID',
                    hover_name='LabName',
                    hover_data=['LabDateTime', 'LabUnits'],
                    facet_col='LabName',
                    facet_col_wrap=5,
                    markers=True,
                    labels={
                        'DayInHospital': 'Days in Hospital',
                        'AdmissionID': 'Nth Admisssion'
                    }
                )
                (fig.update_yaxes(matches=None, title=None)
                 .add_annotation(x=-0.01, y=0.5,
                                 text='Lab Measured Values (hover for units)',
                                 textangle=-90, xref='paper', yref='paper',
                                 font=dict(size=10))
                 .for_each_yaxis(
                     lambda yaxis: yaxis.update(showticklabels=True))
                 .for_each_annotation(
                     lambda a: a.update(text=a.text.split(":")[-1].lower()))
                 .update_layout(hovermode='x unified', font=dict(size=8))
                 .update_traces(marker=dict(size=3))
                 )
            else:
                fig = None
            lab_figs[super_set] = fig
        return lab_figs

    def browser(self, info: _pd.DataFrame, figs: dict, port: int):
        """ Opens a new browser page housing the individuals information

        Args:
            info (pd.DataFrame):
                Table of core information given by get_core_info()
            figs (dict):
                Dictionary of figures to plot, passed in from get_lab_info()
            port (int):
                The port number to start the dash server in

        Returns: None
        """
        applog = _logging.getLogger('Individual Summary')
        app = _dash.Dash('Individual Summary')
        html_out = [
            _html.H1(children='Patient: ' + info['Values'].iloc[0]),
            _html.H3('Characteristics'),
            _html.Table([
                _html.Thead(_html.Tr([
                        _html.Th(col)
                        for col in info.columns])),
                _html.Tbody([_html.Tr([
                    _html.Td(info.iloc[i][col])
                    for col in info.columns])
                    for i in range(len(info))])
            ]),
            _html.H3('Lab History')
        ]
        for plot in figs.keys():
            figs[plot].update_layout(title=None)
            html_out.append(_html.H2(children=plot))
            html_out.append(_dcc.Graph(id=plot, figure=figs[plot]))

        app.layout = _html.Div(children=html_out)

        applog.handlers = []
        _wb.open_new('http://127.0.0.1:' + str(port) + '/')
        app.run_server(port=port)
        return None


class QuickSearch:
    """
    Opens a webbrowser to filter the dataframes, can be used to search for
    specific patients more easily.
    Users may want to copy the patients ID for use in the IndSummary()
    """

    def __init__(self, dfs: dict):
        """ Initializes the class

        Args:
            dfs (dict):
                The id of the patient whose summary data is requested
        """

        self.dfs = dfs
        date = _pd.to_datetime(dfs['patients']['PatientDateOfBirth']).dt.date
        self._min_year = date.min().year
        self._max_year = date.max().year
        self._min_admit = self.dfs['admissions']['AdmissionID'].min()
        self._max_admit = self.dfs['admissions']['AdmissionID'].max()

    def __call__(self, port: int = 8050):
        """
        Opens a new browser window with filters to search through the data
        Sets up the dashboard layout and inputs/outputs

        Args:
            port (int, optional):
                Port to open the interactive server on.
                Defaults to 8050.
        """
        applog = _logging.getLogger('Quick Search')
        app = _dash.Dash('Quick Search')
        info = self.dfs['patients']
        diag = self.dfs['diagnosis']

        inputs = _html.Div(children=[
            _html.H2('Patient Search - Filters'),
            _html.Label('Maximum Rows to Show'),
            _dcc.Slider(id='max_rows',
                        min=1, max=20, value=10,
                        marks={i: f'Row {i}' for i in range(1, 21)}),
            _html.H3('Patient Info'),
            _html.Label('Patient Sex'),
            _dcc.Dropdown(id='sex',
                          options=self._dropdown(info['PatientGender'])),
            _html.Label('Year Born'),
            _dcc.RangeSlider(id='dob',
                             tooltip={'placement': 'top'},
                             min=self._min_year, max=self._max_year,
                             value=[self._min_year, self._max_year],
                             marks={i: str(i) for i in range(
                                 self._min_year, self._max_year + 1, 10)}),
            _html.Label('Patient Race'),
            _dcc.Dropdown(id='race',
                          options=self._dropdown(info['PatientRace'])),
            _html.Label('Patient Marital Status'),
            _dcc.Dropdown(id='marital',
                          options=self._dropdown(info['PatientMaritalStatus'])),
            _html.Label('Patient Language'),
            _dcc.Dropdown(id='lang',
                          options=self._dropdown(info['PatientLanguage'])),
            _html.Label('Minimum Number of Admissions'),
            _dcc.Slider(id='admit',
                        min=self._min_admit, max=self._max_admit,
                        value=1,
                        marks={i: i for i in range(
                            self._min_admit, self._max_admit + 1)}),
            _html.Label('Known Primary Diagnosis Codes'),
            _dcc.Dropdown(id='pdc',
                          options=self._dropdown(diag['PrimaryDiagnosisCode']),
                          multi=True
                          )
        ])
        outputs = _html.Div(children=[
            _html.H1('Dataframes Found'),
            _html.Div(id='tables')
        ])

        app.layout = _html.Div(children=[inputs, outputs])
        callback_components = app.callback(_Output('tables', 'children'),
                                           _Input('max_rows', 'value'),
                                           _Input('sex', 'value'),
                                           _Input('dob', 'value'),
                                           _Input('race', 'value'),
                                           _Input('marital', 'value'),
                                           _Input('lang', 'value'),
                                           _Input('admit', 'value'),
                                           _Input('pdc', 'value'))
        callback_components(self.tables_out)

        applog.handler = []
        _wb.open_new('http://127.0.0.1:' + str(port) + '/')
        app.run_server(port=port)

    def tables_out(self,
                   max_rows,
                   sex,
                   birthday,
                   race,
                   marital,
                   language,
                   admittance,
                   diag_code):
        """
        Uses the dash callback to dynamically update the table outputs
        based on the inputs of the dash-core-components widgets

        Args:
            max_rows (int):
                Maximum rows to print the output tables
            sex (str):
                Patient gender filter
            birthday (list):
                Year of birth filter
            race (str):
                Patient race filter
            marital (str):
                Patient marital status filter
            language (str):
                Patient language filter
            admittance (int):
                Patient minimum times admitted filter
            diag_code ([str):
                Diagnosis codes filter

        Returns:
            list:
                List of html tables to print as output for dash server
        """
        filtered_dfs = _copy(self.dfs)

        self.filter_str(filtered_dfs, 'patients', 'PatientGender',
                        sex)
        self.filter_str(filtered_dfs, 'patients', 'PatientRace',
                        race)
        self.filter_str(filtered_dfs, 'patients', 'PatientMaritalStatus',
                        marital)
        self.filter_str(filtered_dfs, 'patients', 'PatientLanguage',
                        language)
        self.filter_str(filtered_dfs, 'diagnosis', 'PrimaryDiagnosisCode',
                        diag_code, is_list=True)
        self.filter_num(filtered_dfs, 'patients', 'PatientDateOfBirth',
                        min(birthday), 'min', date=True)
        self.filter_num(filtered_dfs, 'patients', 'PatientDateOfBirth',
                        max(birthday), 'max', date=True)
        for df_name in ['diagnosis', 'admissions', 'labs']:
            self.filter_num(filtered_dfs, df_name, 'AdmissionID',
                            admittance, 'min')
        
        self.update_remaining_tables(filtered_dfs, 'diagnosis')
        self.update_remaining_tables(filtered_dfs, 'patients')

        df_order = ['patients', 'diagnosis', 'admissions', 'labs']
        df_order = [x for x in df_order if x in filtered_dfs.keys()]
        children_out = [
            _html.H4(f'{filtered_dfs["patients"].shape[0]} - Patients Found'),
            _html.Div([_html.Div(
                [_html.H3(key),
                 self.html_table(filtered_dfs[key], max_rows)]
            ) for key in df_order])
        ]
        return children_out

    def _dropdown(self, column: _pd.Series):
        """ Creates the dash dropdown dictionary

        Args:
            column (pd.Series):
                The pandas series to convert into a dropdown menu

        Returns:
            dict:
                Dictionary for use with dcc.Dropdown
        """
        return [{'label': i, 'value': i} for i in sorted(column.unique())]

    def update_remaining_tables(self, dfs: dict, df_key: str):
        """ Update the remaining tables, filtering out non-matching patient IDs

        Args:
            dfs (dict):
                Dictionary of dataframes to filter
            df_key (str):
                The filtered dataframe
                all other dataframes will update based on this
        """

        fltrd_patients = dfs[df_key]['PatientID'].unique()
        for key in dfs.keys():
            if key != df_key:
                dfs[key] = dfs[key][dfs[key]['PatientID'].isin(fltrd_patients)]

    def html_table(self, df: _pd.DataFrame, max_rows: int):
        """ Convert pandas dataframe to html table

        Args:
            df (pd.DataFrame):
                Pandas dataframe to conevrt to html
            max_rows (int):
                Maximum rows to convert to html
                (to prevent too many being printed)

        Returns:
            [html.Table]:
                The pandas dataframe in a html form
        """

        return _html.Table([
            _html.Thead(_html.Tr([_html.Th(col) for col in df.columns])),
            _html.Tbody([_html.Tr(
                [_html.Td(df.iloc[i][col]) for col in df.columns]
            ) for i in range(min(len(df), max_rows))
            ])
        ])

    def filter_num(self, dfs: _pd.DataFrame, key: str, column: str,
                   value: int, minmax: str = 'min', date=False):
        """
        Filters the given dataframe given a numeric input
        Updates the dataframe in place

        Args:
            dfs (pd.DataFrame):
                Dictionary of dataframes to filter
            key (str):
                Key for dataframe wanted to filter
            column (str):
                String of column name to filter
            value (int):
                Value to be compared
            minmax (str, optional):
                Comparison request, can be 'min', 'max' or 'exact'.
                Defaults to 'min'.
            date (bool, optional):
                Set True if a datetime column is being put it.
                Defaults to False.

        Returns:
            None

        """
        
        if value is not None:
            if date:
                filter_col = _pd.DatetimeIndex(dfs[key][column]).year
            else:
                filter_col = dfs[key][column]
            if minmax == 'min':
                dfs[key] = dfs[key][filter_col >= value]
            elif minmax == 'max':
                dfs[key] = dfs[key][filter_col <= value]
            elif minmax == 'exact':
                dfs[key] = dfs[key][filter_col == value]

    def filter_str(self, dfs: _pd.DataFrame, key: str, column: str,
                   text, is_list: bool=False):
        """
        Filters the given dataframe given a string input
        Updates the dataframe in place

        Args:
            dfs (pd.DataFrame):
                Dictionary of dataframes to filter
            key (str):
                Key for dataframe wanted to filter
            column (str):
                String of column name to filter
            text (str or list):
                String(s) to be compared
                If the text given is 'Unknown' it won't filter anything
            is_list (bool):
                Uses pandas 'isin' instead if True.
                Defaults to False.

        Returns:
            None

        """
        if text is not None and text != 'Unknown':
            if is_list:
                dfs[key] = dfs[key][dfs[key][column].isin(text)]
            else:
                dfs[key] = dfs[key][dfs[key][column] == text]

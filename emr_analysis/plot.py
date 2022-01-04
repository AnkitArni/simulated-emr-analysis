import re as _re
import webbrowser as _wb
import pandas as _pd
import numpy as _np
import plotly.express as _px
import dash as _dash
from dash import dcc as _dcc
from dash import html as _html


def summary() -> None:
    print('Hello there')
    
def ind_summary(patient_id: str, dfs: dict, browser: bool = False):
    core_info = dfs["PatientCorePopulatedTable"]
    cols = core_info.columns
    col_dict = {x:_re.sub("Patient|(\\w)([A-Z])", "\\1 \\2", x).strip() for x in cols}
    col_dict["PatientID"] = "ID"
    core_info = core_info.rename(columns=col_dict)
    
    core_info = core_info[core_info["ID"] == patient_id]
    core_info = core_info.melt()
    core_info.columns = ["Patient_Info","values"]
    
    
    lab_info = dfs["LabsCorePopulatedTable"]
    lab_info = lab_info[lab_info['PatientID'] == patient_id]
    lab_info = lab_info.assign(LabDateTime=_pd.to_datetime(lab_info['LabDateTime']).dt.date)
    lab_info = lab_info.sort_values(by="LabDateTime")

    tmp = (lab_info[['AdmissionID','LabName','LabDateTime']]
           .groupby(['AdmissionID', 'LabName'])
           .min()
           .reset_index()
           .rename(columns={'LabDateTime':'StartDate'})
          )
    
    lab_info = lab_info.merge(tmp, how = 'left', on=['AdmissionID','LabName'])
    lab_info['DayInHospital'] = (lab_info['LabDateTime'] - lab_info['StartDate']).dt.days
    
    lab_figs = {}
    for super_set in {x.split(':')[0] for x in dfs['LabsCorePopulatedTable']['LabName']}:
        lab_fig_data = lab_info[lab_info['LabName'].str.contains(super_set)]
    
        if not lab_fig_data.empty:
            fig = _px.line(
                lab_fig_data,
                x='DayInHospital',
                
                hover_name='LabName', hover_data=['LabDateTime', 'LabUnits'],
                
                y='LabValue',
                color='AdmissionID',
                facet_col='LabName',
                facet_col_wrap=5,
                markers=True
            )
            fig.update_layout(hovermode="x unified")
            (fig.update_yaxes(matches=None)
             .for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
             .for_each_annotation(lambda a: a.update(text=a.text.split(":")[-1].lower()))
             .update_layout(font=dict(size=8))
             .update_traces(marker=dict(size=3))
            )

        else: fig = None
        
        lab_figs[super_set.lower()] = fig
    
    if browser:
        app = _dash.Dash()
        html_out = [
                _html.H1(children='Hello Dash'),
                _html.Div(children='A web app framework')
            ]
        for plot in lab_figs.keys():
            html_out.append(_dcc.Graph(id=plot, figure=lab_figs[plot]))
            
        app.layout = _html.Div(children=html_out)
        
        _wb.open_new('http://127.0.0.1:8050/')
        app.run_server()
        
        return None
    
    else:
        return core_info, lab_figs
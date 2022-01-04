import os as _os
import pandas as _pd
import numpy as _np
import typing as _ty
import tkinter as _tk
from zipfile import ZipFile as _zf

_base = _os.path.dirname(_os.path.realpath(__file__))

def load(option: int = 1) -> None:
    print('Hello there')

def load_example():
    dfs = dict()
    with _zf(_base + "/examples/100-Patients.zip") as z:
        files = [x for x in z.namelist() if x.endswith('.txt') and 'readme' not in x.lower()]
        #print(files)
        for file in files:
            with z.open(file, 'r') as f:
                key = file.replace('.txt', '')
                dfs[key] = _pd.read_csv(f, header=0, delimiter='\t')
    return dfs
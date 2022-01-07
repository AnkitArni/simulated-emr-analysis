import os as _os
import re as _re
import pandas as _pd
import typing as _ty
import tkinter as _tk
import traceback as _tb
from pathlib import PurePath
from zipfile import ZipFile as _zf
from magic import from_file as magic_from_file
from tkinter.filedialog import askopenfilename

class Loader:
    BASE_PATH = _os.path.realpath(__file__)
    EXAMPLE_ZIP_PATH = _os.path.join(_os.path.dirname(BASE_PATH), 'examples', '100-Patients.zip')
    LOAD_OP_TYPES = {'example', 'custom'}
    EMR_FILE_TYPES = {'text/plain': '.txt', 'application/zip': '.zip'}
    EMR_CONTENT_TYPES = {
        'admissions': _re.compile(r"^[Pp]atient[Ii][Dd].+[Aa]dmission[Ss]tart[Dd]ate.*"),
        'diagnosis': _re.compile(r"^[Pp]atient[Ii][Dd].+[Dd]iagnosis[Cc]ode.*"),
        'labs': _re.compile(r"^[Pp]atient[Ii][Dd].+[Ll]ab[Nn]ame.*"),
        'patients': _re.compile(r"^[Pp]atient[Ii][Dd].+[Pp]atient(?:[Dd]ate[Oo]f[Bb]irth|[Dd][Oo][Bb]).*")
    }
    def __init__(self) -> None:
        self.emr_data = {}

    def __call__(self, load_op: str, dialog: bool = True) -> _ty.Dict[str, _pd.DataFrame]:
        if load_op in __class__.LOAD_OP_TYPES:
            if load_op == 'example':
                input_file_path = __class__.EXAMPLE_ZIP_PATH
                self.process_zipfile_load(input_file_path)
            elif load_op == 'custom':
                if dialog:
                    input_file_path = self.get_file_from_dialog()
                    input_file_type = self.check_file_type(input_file_path)
                else:
                    valid_input = False
                    while not valid_input:
                        input_file_path_raw = input('Please enter the input file path: ')
                        print(input_file_path_raw)
                        input_file_path = _os.path.realpath(input_file_path_raw)
                        print(input_file_path)
                        input_file_type = self.check_file_type(input_file_path)
                        if _os.path.isfile(input_file_path) and input_file_type in {'application/zip', 'text/plain'}:
                            valid_input = True
                if input_file_type == 'application/zip':
                    self.process_zipfile_load(input_file_path)
                elif input_file_type == 'text/plain':
                    self.process_textfile_load(input_file_path)
        return self.emr_data

    def get_file_from_dialog(self) -> str:
        root = _tk.Tk()
        root.wm_attributes('-topmost', 1)
        root.withdraw()
        input_file_path = askopenfilename(
            parent = root,
            title = 'Select a file to open',
            filetypes = (('Text files', '*.txt'), ('Zip files', '*.zip'), ('All files', '*.*'))
            # filetypes = [('Zip files', '*.zip')]
        )
        root.destroy()
        return input_file_path

    def check_file_type(self, input_file_path: str = '') -> str:
        input_file_type = magic_from_file(input_file_path, mime = True)
        return input_file_type

    def process_zipfile_load(self, zipfile_path: str = '') -> None:
        try:
            with _zf(zipfile_path, mode = 'r') as zipfile_pointer:
                zipfile_contents = zipfile_pointer.infolist()
                for zipfile_entry in zipfile_contents:
                    if PurePath(zipfile_entry.filename).suffix.endswith(__class__.EMR_FILE_TYPES['text/plain']):
                        with zipfile_pointer.open(zipfile_entry.filename, mode = 'r') as file_pointer:
                            print(type(file_pointer))
                            self.extract_data_from_textfile(file_pointer, encoded = True)
        except:
            _tb.print_exc()

    def process_textfile_load(self, textfile_path: str = '') -> None:
        try:
            if PurePath(textfile_path).suffix.endswith(__class__.EMR_FILE_TYPES['text/plain']):
                with open(textfile_path, mode = 'r') as file_pointer:
                    print(type(file_pointer))
                    self.extract_data_from_textfile(file_pointer, encoded = False)
        except:
            _tb.print_exc()

    def extract_data_from_textfile(self, file_pointer, encoded: bool) -> None:
        for line in file_pointer:
            if len(line.strip()) > 0:
                header = f"{line.strip().decode('utf-8-sig')}" if encoded else f"{line.strip()}"
                break
        content_type = self.get_emr_content_type(header)
        if content_type is not None:
            data = _pd.read_csv(file_pointer, delimiter = '\t', encoding = 'utf-8-sig')
            self.emr_data[content_type] = data

    def get_emr_content_type(self, header: str = '') -> str:
        for content_type, pattern in __class__.EMR_CONTENT_TYPES.items():
            if bool(_re.match(pattern, header)):
                return content_type

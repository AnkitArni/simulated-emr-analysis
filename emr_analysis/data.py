import os as _os
import re as _re
import pandas as _pd
import typing as _ty
import logging as _lg
import tkinter as _tk
from sys import stdout as _stdout
from zipfile import ZipFile as _zf
from magic import from_file as _magic_from_file
from tkinter.filedialog import askopenfilename as _tk_filedialog

_BASE_PATH = _os.path.realpath(__file__)
_lg.basicConfig(stream = _stdout, level = _lg.INFO)
_LOGGER = _lg.Logger(name = __file__)

class Loader:
    EXAMPLE_ZIP_PATH = _os.path.join(
        _os.path.dirname(_BASE_PATH),
        'examples',
        '100-Patients.zip')
    EMR_FILE_ENC = 'utf-8-sig'
    LOAD_TYPES = {'example', 'zip', 'text'}
    EMR_FILE_TYPES = {'text/plain', 'application/zip'}
    EMR_PATTERNS = {
        'admissions': {
            'FILENAME': _re.compile(r"^[Aa]dmissions[Cc]ore.+\.[Tt][Xx][Tt]"),
            'HEADER': _re.compile(r"^[Pp]atient[Ii][Dd].+[Aa]dmission[Ss]tart[Dd]ate.*"),
        },
        'diagnosis': {
            'FILENAME': _re.compile(r"^[Aa]dmissions[Dd]iagnoses[Cc]ore.+\.[Tt][Xx][Tt]"),
            'HEADER': _re.compile(r"^[Pp]atient[Ii][Dd].+[Dd]iagnosis[Cc]ode.*"),
        },
        'labs': {
            'FILENAME': _re.compile(r"^[Ll]abs[Cc]ore.+\.[Tt][Xx][Tt]"),
            'HEADER': _re.compile(r"^[Pp]atient[Ii][Dd].+[Ll]ab[Nn]ame.*"),
        },
        'patients': {
            'FILENAME': _re.compile(r"^[Pp]atient[Cc]ore.+\.[Tt][Xx][Tt]"),
            'HEADER': _re.compile(r"^[Pp]atient[Ii][Dd].+[Pp]atient(?:[Dd]ate[Oo]f[Bb]irth|[Dd][Oo][Bb]).*")
        }
    }

    def __call__(
        self, load_type: str,
        input_file_path: str = '',
        append: bool = False,
        dialog: bool = False
    ) -> _ty.Union[_ty.Dict[str, _pd.DataFrame], _ty.List[_ty.Tuple[str, _pd.DataFrame]]]:
        """Entry point for the Loader object.

        Args:
            load_type (str):
                Controls the type of inpu file loading.
                Can only be one of 'example', 'text' or 'zip'.
            input_file_path (str, optional):
                Absolute path of the zip or text file to load.
                File type must match with 'load_type' argument value.
                Arguments 'append' and 'dialog' are ignored when this is set.
                Defaults to ''.
            append (bool, optional):
                Flag to control the return value.
                Only applicable when argument 'load_type' is 'text'.
                Defaults to False.
            dialog (bool, optional):
                Flag to control whether to use a Tkinter dialog box to load the file.
                Defaults to False.

        Returns:
            _ty.Union[_ty.Dict[str, _pd.DataFrame], _ty.List[_ty.Tuple[str, _pd.DataFrame]]]:
                Returns either:
                1. A list containing a single tuple of content type and DataFrame, or
                2. A dictionary with content type as keys and DataFrame as values.
        """
        _LOGGER.debug('__call__: Start')
        load_type = load_type.lower()
        if load_type in __class__.LOAD_TYPES:
            if load_type == 'example':
                input_file_path = __class__.EXAMPLE_ZIP_PATH
                dfs = self.__process_zipfile_load(input_file_path)
                _LOGGER.debug('__call__: End')
                return dfs
            else:
                if input_file_path == '':
                    if dialog:
                        valid_input = False
                        while not valid_input:
                            input_file_path = self.__get_file_from_dialog(load_type)
                            if input_file_path != '':
                                input_file_type = self.__check_file_mimetype(input_file_path)
                                if input_file_type in __class__.EMR_FILE_TYPES:
                                    valid_input = True
                            else:
                                _LOGGER.warning(
                                    'Since no file was selected by the user, '
                                    + 'no data was loaded'
                                )
                                _LOGGER.debug('__call__: End')
                                return dict()
                    else:
                        valid_input = False
                        while not valid_input:
                            input_file_path_raw = input(
                                'Please enter the input file absolute path '
                                + '(or "exit" to cancel): '
                            )
                            try:
                                input_file_path = _os.path.realpath(input_file_path_raw)
                                if input_file_path_raw.strip().lower() == 'exit':
                                    _LOGGER.warning(
                                        'Since no file was entered by the user, '
                                        + 'no data was loaded'
                                    )
                                    _LOGGER.debug('__call__: End')
                                    return dict()
                                elif _os.path.isfile(input_file_path):
                                    input_file_type = self.__check_file_mimetype(
                                        input_file_path)
                                    if input_file_type in __class__.EMR_FILE_TYPES:
                                        _LOGGER.debug(
                                            f'input_file_path = {input_file_path}')
                                        valid_input = True
                            except BaseException:
                                _LOGGER.exception('Could not recognise the given file')
                else:
                    try:
                        if _os.path.isfile(input_file_path):
                            input_file_type = self.__check_file_mimetype(input_file_path)
                    except BaseException:
                        _LOGGER.exception('Could not recognise the given file')
                if load_type == 'zip' and input_file_type == 'application/zip':
                    dfs = self.__process_zipfile_load(input_file_path)
                    _LOGGER.debug('__call__: End')
                    return dfs
                elif load_type == 'text' and input_file_type == 'text/plain':
                    content_type, data = self.__process_textfile_load(
                        input_file_path)
                    if append:
                        _LOGGER.debug('__call__: End')
                        if content_type != '':
                            return [(content_type, data)]
                        else:
                            _LOGGER.warning('Could not identify a valid EMR file type, '
                            + 'no data was loaded'
                            )
                            return list()
                    else:
                        dfs = {}
                        if content_type != '':
                            dfs[content_type] = data
                        else:
                            _LOGGER.warning('Could not identify a valid EMR file type, '
                            + 'no data was loaded'
                            )
                        _LOGGER.debug('__call__: End')
                        return dfs
                else:
                    _LOGGER.warning(
                        '"load_type" and "input_file_path" MIME type '
                        + 'did not match, no data was loaded'
                    )
                    return dict()

    def __get_file_from_dialog(self, load_type: str) -> str:
        """Select and load a file using a Tkinter file dialog box.

        The only formats supported are either text (.txt) or zip (.zip) files.

        Args:
            load_type (str):
                Controls the type of inpu file loading.
                Can only be one of 'example', 'text' or 'zip'.

        Returns:
            input_file_path (str):
                Absolute path of the file to load.
        """
        _LOGGER.debug('get_file_from_dialog: Start')
        root = _tk.Tk()
        root.wm_attributes('-topmost', 1)
        root.withdraw()
        if load_type == 'zip':
            input_file_path = _tk_filedialog(
                parent = root,
                title = 'Select a zip file to load',
                filetypes = [('Zip files', '*.zip')]
            )
        elif load_type == 'text':
            input_file_path = _tk_filedialog(
                parent = root,
                title = 'Select a text file to load',
                filetypes = [('Text files', '*.txt')]
            )
        root.destroy()
        _LOGGER.debug('get_file_from_dialog: End')
        return input_file_path

    def __check_file_mimetype(self, input_file_path: str = '') -> str:
        """Get the MIME type of a file using the python-magic library.

        Requires the C-language dependency libmagic to function.

        Args:
            input_file_path (str, optional):
                Absolute path of the file to check. Defaults to ''.

        Returns:
            input_file_mimetype (str):
                MIME type of the given file.
        """
        input_file_mimetype = _magic_from_file(input_file_path, mime = True)
        return input_file_mimetype

    def __process_zipfile_load(
        self, zipfile_path: str = '') -> _ty.Dict[str, _pd.DataFrame]:
        """Processes the given zip file to load data from.

        Searches for text files matching the required data to load data from.

        Args:
            zipfile_path (str, optional):
                Absolute path to the given zip file. Defaults to ''.

        Returns:
            dfs (_ty.Dict[str, _pd.DataFrame]):
                Dictionary with content type as keys and DataFrame as values.
        """
        _LOGGER.debug('process_zipfile_load: Start')
        try:
            dfs = {}
            with _zf(zipfile_path, mode = 'r') as zipfile_pointer:
                zipfile_contents = zipfile_pointer.infolist()
                for zipfile_entry in zipfile_contents:
                    filename_type = ''
                    for fn_type, pattern in __class__.EMR_PATTERNS.items():
                        if bool(_re.match(pattern['FILENAME'], zipfile_entry.filename)):
                            filename_type = fn_type
                    if filename_type != '':
                        with zipfile_pointer.open(
                            zipfile_entry.filename, mode = 'r') as file_pointer:
                            content_type, data = self.__extract_data_from_textfile(
                                file_pointer)
                            dfs[content_type] = data
            _LOGGER.debug('process_zipfile_load: End')
            return dfs
        except BaseException:
            _LOGGER.exception('Could not process the given zip file')

    def __process_textfile_load(
            self, textfile_path: str = '') -> _ty.Tuple[str, _pd.DataFrame]:
        """Processes the given text file to load data from.

        Args:
            textfile_path (str):
                Absolute path to the given text file. Defaults to ''.

        Returns:
            content_type, data (_ty.Tuple[str, _pd.DataFrame]):
                Tuple of the content type and the corresponding DataFrame.
        """
        _LOGGER.debug('process_textfile_load: Start')
        try:
            with open(textfile_path, mode = 'rb') as file_pointer:
                header = self.__check_textfile_header(file_pointer)
                if header != '':
                    content_type, data = self.__extract_data_from_textfile(
                        file_pointer)
                    _LOGGER.debug('process_textfile_load: End')
                    return content_type, data
        except BaseException:
            _LOGGER.exception('Could not process the given text file')

    def __check_textfile_header(self, file_pointer: _ty.TextIO) -> str:
        header = ''
        try:
            for line in file_pointer:
                if len(line.strip()) > 0:
                    header = f'{line.strip().decode(__class__.EMR_FILE_ENC)}'
                    break
            file_pointer.seek(0)
            return header
        except BaseException:
            _LOGGER.exception('Could not decode the textfile header line')

    def __extract_data_from_textfile(
            self, file_pointer: _ty.TextIO) -> _ty.Tuple[str, _pd.DataFrame]:
        """Reads through the file and converts it to a Pandas DataFrame.

        Args:
            file_pointer (_ty.TextIO):
                File-like object used to read through the file.

        Returns:
            content_type, data (_ty.Tuple[str, _pd.DataFrame]):
                Tuple of the content type and the corresponding DataFrame.
        """
        _LOGGER.debug('extract_data_from_textfile: Start')
        header = self.__check_textfile_header(file_pointer)
        if header is not None and header != '':
            data = _pd.DataFrame()
            try:
                content_type = self.__get_emr_content_type(header)
                if content_type is not None and content_type != '':
                    data = _pd.read_csv(
                        file_pointer,
                        delimiter = '\t',
                        encoding = __class__.EMR_FILE_ENC)
                    _LOGGER.debug('extract_data_from_textfile: End')
            except BaseException:
                _LOGGER.exception('Could not read data from the given file')
            finally:
                return content_type, data

    def __get_emr_content_type(self, header: str) -> str:
        """Check text file header against supported header patterns.

        Uses regex to match header string against supported header patterns.

        Args:
            header (str):
                Header line of a text file.

        Returns:
            content_type (str):
                One of the supported content types determined from pattern matching.
        """
        content_type = ''
        if header is not None and header != '':
            for c_type, pattern in __class__.EMR_PATTERNS.items():
                if bool(_re.match(pattern['HEADER'], header)):
                    content_type = c_type
                    break
        return content_type

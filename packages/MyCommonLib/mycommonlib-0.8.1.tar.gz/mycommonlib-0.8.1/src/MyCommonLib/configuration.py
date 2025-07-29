import logging
from os import path
from pathlib import Path, PosixPath

import yaml
from rich.console import Console
from rich.panel import Panel
from MyCommonLib.software_mode import softMode

from MyCommonLib.constants import COLOR, FMODE, defLogFile
from MyCommonLib.dictman import dict2Table
from MyCommonLib.loginit import logInit


class Loader(yaml.SafeLoader):
    """Add to the YAML standar class the command !include to include slave yaml file"""

    def __init__(self, stream):
        self._root = path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)


Loader.add_constructor('!include', Loader.include)


def read_yaml(fileName: Path) -> dict:
    """
    Read a YAML File with the extended loader

    Args:
        fileName (Path): The file to load

    Raises:
        FileNotFoundError: The file to read not exists

    Returns:
        dict: The dictionary in the file
    """
    if type(fileName) is str:
        fileName = Path(fileName)
    if not fileName.exists():
        raise FileNotFoundError
    with open(fileName, FMODE.READ) as f:
        # return yaml.safe_load(f)
        return yaml.load(f, Loader)


def write_yaml(data:dict, fileName:Path, overwrite:bool=False):

    if not type(data) is dict:
        raise TypeError
    if type(fileName) is str:
        fileName=Path(fileName)
    if fileName.exists() and not overwrite:
        raise FileExistsError
    with open(fileName, FMODE.WRITE) as file:
        documents = yaml.dump(data, file)


class Configure:
    """Configuration class"""
    
    configFile:Path = None
    """Name of the configuration file to load"""
    
    def __init__(self):
        self._name = "Software Configuration"
        self._logger = 'MyLogger'
        self._debug = False
        self._verbose = 0
        self.configFile = None
        self._logFile = None
        self.console: Console = softMode.console
        self._dict_exclude=['log']
        self.log=None
        self.log_mode = FMODE.APPEND
        self.log_formatter = '{asctime} | {levelname:8} | {name:10} | {module:12} | {funcName:20} | {lineno:4} | {message}'
        
    def start_log(self,file_mode: str = FMODE.APPEND):
        self.log = logInit(logger=self._logger,
                           logLevel=logging.INFO,
                           formatter=self.log_formatter,
                           fileMode=file_mode)

    @property
    def logFile(self):
        return self._logFile

    @logFile.setter
    def logFile(self, value: Path):
        
        self._logFile = value.expanduser()
        if not self._logFile.parent.exists():
            self._logFile.parent.mkdir(parents=True)
        self.log.removeHandler(self.log.handlers[0])
        file_handler = logging.FileHandler(self._logFile, mode=self.log_mode)
        formatter = logging.Formatter(self.log_formatter,
                                      datefmt='%m/%d/%Y %I:%M:%S %p',
                                      style="{")
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)
        # self.log = logInit(logFile=value, logger=self._logger,
        #                    logLevel=logging.INFO, fileMode=FMODE.APPEND)
        self.log_file = value.as_posix()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
        if value:
            if self._logFile is not None:
                self.log.setLevel(logging.DEBUG)
                self.log.debug("Set the loglevel to Debug", verbosity=1)
            softMode.debug = value
        else:
            if self._logFile is not None:
                self.log.setLevel(logging.INFO)
            softMode.debug = False
        self.debug_status = value

    @property
    def verbose(self) -> int:
        return self._verbose

    @verbose.setter
    def verbose(self, value: int):
        self._verbose = value
        softMode.verbose = value
        self.verbose_status=f"Level {value}"

    def verbosity(self, level: int = 0) -> bool:
        """
        Compare the value with the verbosity level stored in the configuration class.
        Usually is used to check if some information will be printed or not

        Args:
            level (int, optional): level to check. Defaults to 0.

        Returns:
            bool: True if the current level is higher or equal to the configurated one
        """
        return softMode.check(level)

    def toDict(self) -> dict:
        ret = {}
        for item in self.__dict__:
            if not item.startswith('_') and not item in self._dict_exclude:
                elem = getattr(self, item)
                if type(elem) is PosixPath:
                    ret[item] = str(elem)
                else:
                    ret[item] = elem
        return dict(sorted(ret.items()))

    def Show(self):
        pn = Panel(dict2Table(self.toDict()), title=self._name,
                   expand=False, border_style=COLOR.panel)
        self.console.print(pn)

    def setLog(self, value: Path = None, default: bool = False):
        if default:
            self.logFile = Path('/var/log').joinpath(defLogFile)
        else:
            self.logFile = value

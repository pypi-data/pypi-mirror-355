from rich.progress import BarColumn, SpinnerColumn, TimeElapsedColumn
from pathlib import Path
import pkg_resources


VERSION = pkg_resources.get_distribution('MyCommonLib').version

progEpilog = "- For any information or suggestion please contact " \
    "[bold magenta]Romolo.Politi@inaf.it[/bold magenta]"


class MSG:
    ERROR = "[red][ERROR][/red] "
    CRITICAL = "[red][CRITICAL][/red] "
    INFO = "[green][INFO][/green] "
    DEBUG = "[blue][DEBUG][/blue] "
    WARNING = "[yellow][WARNING][/yellow] "


class MSGType:
    ERROR = {'title': 'ERROR', 'color': 'red'}
    CRITICAL = {'title': 'CRITICAL', 'color': 'red'}
    WARNING = {'title': "WARNING", 'color': 'yellow'}


class FMODE:
    READ = 'r'
    READ_BINARY = 'rb'
    WRITE = 'w'
    WRITE_BINARY = 'wb'
    APPEND = 'a'


class COLOR:
    console = 'dodger_blue3'
    error = 'red'
    panel = 'yellow'

progresSet = [SpinnerColumn(finished_text=':thumbs_up-emoji:'),
              "[progress.description]{task.description}",
              BarColumn(finished_style='green'),
              "[progress.percentage]{task.percentage:>3.0f}%",
              "{task.completed:>6d} of {task.total:6d}",
              TimeElapsedColumn()
              ]

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

defLogFile = 'software_logger.log'

debug_help_text = "Enable :point_right: [yellow]debug mode[/yellow] :point_left:"
verbose_help_text = "Enable :point_right: [yellow]verbose mode[/yellow] :point_left:"

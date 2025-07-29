from pathlib import PosixPath

from rich.markdown import Markdown
from rich.table import Table


def dict2Table_Hor(item: list) -> Table:
    dt = Table()
    for elem in item[0].keys():
        dt.add_column(elem)
    for elem in item:
        dt.add_row(*[str(value) for key, value in elem.items()])
    return dt


def conv(txt: str):
    return ' '.join(txt.split('_')).title()


def dict2Table(item: dict, sep: str = '=') -> Table:
    if not isinstance(item, dict):
        raise ValueError("item must be a dictionary")
    dt = Table.grid()
    dt.add_column(style="bold", justify='right')
    dt.add_column()
    dt.add_column()
    for elem in item.keys():
        if isinstance(item[elem],list):
            if isinstance(item[elem][0], str):
                dt.add_row(conv(elem), f" {sep} ", f"[bold]{item[elem][0]}[/bold]")
                for subElem in item[elem][1:]:
                    dt.add_row("", f" {sep} ", f"[bold]{subElem}[/bold]")
            elif isinstance(item[elem][0], int) or isinstance(item[elem][0], bool):
                dt.add_row(conv(elem), f" {sep} ", f"[bold]{str(item[elem][0])}[/bold]")
                for subElem in item[elem][1:]:
                    dt.add_row("", f" {sep} ", f"[bold]{str(subElem)}[/bold]")
            elif isinstance(item[elem][0],dict):
                dt.add_row(
                    elem,
                    " ",
                    dict2Table_Hor(item[elem]),
                )
                # for subElem in item[elem][1:]:
                #     dt.add_row('','' ,dict2Table(subElem))
        elif isinstance(item[elem],int):
            dt.add_row(conv(elem), f" {sep} ",
                       f"[cyan]{str(item[elem])}[/cyan]")
        elif isinstance(item[elem],bool):
            dt.add_row(conv(elem), f" {sep} ", f"[red]{str(item[elem])}[/red]")
        elif isinstance(item[elem], dict):
            stb = dict2Table(item[elem])
            dt.add_row(conv(elem), " : ", stb)
        elif isinstance(item[elem], PosixPath):
            dt.add_row(conv(elem), f" {sep} ", f"[blue]{str(item[elem])}[/blue]")
        elif item[elem] is None:
            dt.add_row(conv(elem), f" {sep} ", "[blue]None[/blue]")
        else:
            dt.add_row(conv(elem), f" {sep} ", f"[green]{item[elem]}[/green]")
    return dt

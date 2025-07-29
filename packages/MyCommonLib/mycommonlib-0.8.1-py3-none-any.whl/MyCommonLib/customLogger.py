import logging
from io import StringIO
from os import path
from traceback import print_stack

from MyCommonLib.constants import FMODE, MSG
from MyCommonLib.software_mode import softMode


def _is_internal_frame(frame):
    """Signal whether the frame is a CPython or logging module internal."""
    filename = path.normcase(frame.f_code.co_filename)
    if filename == logging._srcfile or "customLogger" in filename:
        return True
    else:
        return False


class SpecialHandler(logging.Handler):
    def emit(self, record) -> None:
        pass

class CustomLogger(logging.Logger):
    def info(self, msg, verbosity=0, *args, **kwargs):
        if softMode.check(verbosity):
            softMode.console.print(f"{MSG.INFO}{msg}")
        # Chiamare il metodo info della classe base per mantenere il comportamento predefinito
        super().info(msg, *args, **kwargs)

    def error(self, msg, verbosity=0, *args, **kwargs):
        if softMode.check(verbosity):
            softMode.console.print(f"{MSG.ERROR}{msg}")
        # Chiamare il metodo info della classe base per mantenere il comportamento predefinito
        super().error(msg, *args, **kwargs)

    def critical(self, msg, verbosity=0, *args, **kwargs):
        if softMode.check(verbosity):
            softMode.console.print(f"{MSG.CRITICAL}{msg}")
        # Chiamare il metodo info della classe base per mantenere il comportamento predefinito
        super().critical(msg, *args, **kwargs)

    def debug(self, msg, verbosity=0, *args, **kwargs):
        if softMode.check(verbosity) and softMode.debug:
            softMode.console.print(f"{MSG.DEBUG}{msg}")
        # Chiamare il metodo info della classe base per mantenere il comportamento predefinito
        super().debug(msg, *args, **kwargs)

    def warning(self, msg, verbosity=0, *args, **kwargs):
        if softMode.check(verbosity):
            softMode.console.print(f"{MSG.WARNING}{msg}")
        # Chiamare il metodo info della classe base per mantenere il comportamento predefinito
        super().warning(msg, *args, **kwargs)

    def findCaller(self, stack_info=True, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is None:
            return "(unknown file)", 0, "(unknown function)", None
        while stacklevel > 0:
            next_f = f.f_back
            if next_f is None:
                # We've got options here.
                # If we want to use the last (deepest) frame:
                break
                # If we want to mimic the warnings module:
                # return ("sys", 1, "(unknown function)", None)
                # If we want to be pedantic:
                # raise ValueError("call stack is not deep enough")
            f = next_f
            if not _is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = None
        if stack_info:
            with StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
        return co.co_filename, f.f_lineno, co.co_name, sinfo

from dataclasses import dataclass
from rich.console import Console


@dataclass
class SoftMode:
    verbose: int
    debug: bool
    console:Console=Console()

    def check(self, level: int = 0) -> bool:
        # self.console.log(f"Verbose: {self.verbose} Level: {level}")
        if not isinstance(level, int):
            level=0
        if self.verbose >= level:
            return True
        else:
            return False

softMode = SoftMode(0,False)
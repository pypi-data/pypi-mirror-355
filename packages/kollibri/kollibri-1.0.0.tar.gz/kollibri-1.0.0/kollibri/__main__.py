from .cli import _parse_cmd_line
from .kollibri import kollibri

kwargs = _parse_cmd_line()

kollibri(**kwargs)

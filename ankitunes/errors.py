import os
from typing import *
from enum import Enum, auto
from aqt.utils import tooltip
class ErrorMode(Enum):
	RAISE=auto()
	SCARY_WARNING = auto()
	HINT = auto()

@overload
def error(msg: str, mode: Literal[ErrorMode.RAISE]) -> NoReturn: ...
@overload
def error(msg: str, mode: ErrorMode = ErrorMode.SCARY_WARNING) -> Union[NoReturn, None]: ...

def error(msg: str, mode: ErrorMode = ErrorMode.SCARY_WARNING) -> Union[NoReturn, None]:
	if os.environ.get('ANKITUNES_TESTING') == '1':
		raise Exception(msg)

	from warnings import warn
	import warnings

	if mode == ErrorMode.HINT:
		tooltip(msg, period=10000)
	elif mode == ErrorMode.RAISE:
		raise Exception(msg)
	elif mode == ErrorMode.SCARY_WARNING:
		warn(msg)
	else:
		warn(msg)

	return None

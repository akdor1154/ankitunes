import os
from typing import *

if os.environ.get('ANKITUNES_HARD_MODE') not in (None, '0', ''):
	def error(msg: str) -> Union[NoReturn, None]:
		raise Exception(msg)
else:
	from warnings import warn
	import warnings
	def error(msg: str) -> Union[NoReturn, None]:
		warn(msg)
		return None
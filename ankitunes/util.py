import typing_extensions
import aqt
from typing import *

def mw() -> aqt.main.AnkiQt:
	if not aqt.mw:
		raise Exception('Main Window doesn\'t exist!')
	return aqt.mw


import typing_extensions
import aqt
import aqt.main
from typing import *


def mw() -> aqt.main.AnkiQt:
	if not aqt.mw:
		raise Exception("Main Window doesn't exist!")
	return aqt.mw
